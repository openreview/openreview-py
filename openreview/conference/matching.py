'''
A module containing tools for matching and and main Matching instance class
'''

from __future__ import division
import os
import csv
import datetime
import json
import random
import string
import openreview
from openreview import Edge
import tld
import re
from tqdm import tqdm
from .. import tools
import time

def _jaccard_similarity(list1, list2):
    '''
    Return a score, indicating the similarity between two lists
    '''
    set1 = set(list1)
    set2 = set(list2)
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)

def _conflict_label(conflicts):
    if len(conflicts) == 0:
        return 'None'

    if any([('@' in c or '~' in c) for c in conflicts]):
        return 'Personal'

    return 'Institutional (level {})'.format(
        max([len(openreview.tools.subdomains(c)) for c in conflicts]))


class Matching(object):
    '''
    Represents a Matching instance.

    Args:
        `conference`: an openreview.Conference object
        `match_group`: an openreview.Group object

    '''
    def __init__(self, conference, match_group, alternate_matching_group=None):
        self.conference = conference
        self.client = conference.client
        self.match_group = match_group
        self.alternate_matching_group = alternate_matching_group
        self.is_reviewer = conference.get_reviewers_id() == match_group.id
        self.is_area_chair = conference.get_area_chairs_id() == match_group.id
        self.is_senior_area_chair = conference.get_senior_area_chairs_id() == match_group.id
        self.is_ethics_reviewer = conference.get_ethics_reviewers_id() == match_group.id
        self.should_read_by_area_chair = conference.get_reviewers_id() == match_group.id and conference.use_area_chairs


    def _get_edge_invitation_id(self, edge_name):
        '''
        Returns a correctly formatted edge invitation ID for this Matching's match group
        '''
        return self.conference.get_invitation_id(edge_name, prefix=self.match_group.id)

    def _get_edge_readers(self, tail):
        readers = [self.conference.id]
        if self.should_read_by_area_chair:
            if self.conference.use_senior_area_chairs:
                readers.append(self.conference.get_senior_area_chairs_id())
            readers.append(self.conference.get_area_chairs_id())
        if self.is_area_chair and self.conference.use_senior_area_chairs:
            readers.append(self.conference.get_senior_area_chairs_id())
        readers.append(tail)
        return readers

    def _create_edge_invitation(self, edge_id, any_tail=False, default_label=None):
        '''
        Creates an edge invitation given an edge name
        e.g. "Affinity_Score"
        '''
        is_assignment_invitation=edge_id.endswith('Assignment') or edge_id.endswith('Aggregate_Score')
        paper_number='{head.number}' if is_assignment_invitation else None

        edge_invitees = [self.conference.get_id(), self.conference.support_user]
        edge_readers = [self.conference.get_id()]
        invitation_readers = [self.conference.get_id()]
        edge_writers = [self.conference.get_id()]
        edge_signatures = [self.conference.get_id() + '$', self.conference.get_program_chairs_id()]
        edge_nonreaders = {
            'values-regex': self.conference.get_authors_id(number='.*')
        }
        if self.is_reviewer:
            if self.conference.use_senior_area_chairs:
                edge_readers.append(self.conference.get_senior_area_chairs_id(number=paper_number))
                invitation_readers.append(self.conference.get_senior_area_chairs_id())
            if self.conference.use_area_chairs:
                edge_readers.append(self.conference.get_area_chairs_id(number=paper_number))
                invitation_readers.append(self.conference.get_area_chairs_id())

            if is_assignment_invitation:
                if self.conference.use_senior_area_chairs:
                    edge_invitees.append(self.conference.get_senior_area_chairs_id())
                    edge_writers.append(self.conference.get_senior_area_chairs_id(number=paper_number))
                    edge_signatures.append(self.conference.get_senior_area_chairs_id(number=paper_number))

                if self.conference.use_area_chairs:
                    edge_invitees.append(self.conference.get_area_chairs_id())
                    edge_writers.append(self.conference.get_area_chairs_id(number=paper_number))
                    edge_signatures.append(self.conference.get_anon_area_chair_id(number=paper_number, anon_id='.*'))

                edge_nonreaders = {
                    'values': [self.conference.get_authors_id(number=paper_number)]
                }

        if self.is_area_chair:
            if self.conference.use_senior_area_chairs:
                edge_readers.append(self.conference.get_senior_area_chairs_id(number=paper_number))
                invitation_readers.append(self.conference.get_senior_area_chairs_id())


            if is_assignment_invitation:
                invitation_readers.append(self.conference.get_area_chairs_id())
                if self.conference.use_senior_area_chairs:
                    edge_invitees.append(self.conference.get_senior_area_chairs_id())
                    edge_writers.append(self.conference.get_senior_area_chairs_id(number=paper_number))
                    edge_signatures.append(self.conference.get_senior_area_chairs_id(number=paper_number))

                edge_nonreaders = {
                    'values': [self.conference.get_authors_id(number=paper_number)]
                }

        if self.is_ethics_reviewer:
            if self.conference.use_ethics_chairs:
                edge_readers.append(self.conference.get_ethics_chairs_id())
                invitation_readers.append(self.conference.get_ethics_chairs_id())

            if is_assignment_invitation:
                if self.conference.use_ethics_chairs:
                    edge_invitees.append(self.conference.get_ethics_chairs_id())
                    edge_writers.append(self.conference.get_ethics_chairs_id())
                    edge_signatures.append(self.conference.get_ethics_chairs_id())

                edge_nonreaders = {
                    'values': [self.conference.get_authors_id(number=paper_number)]
                }                               

        readers = {
            'values-copied': edge_readers + ['{tail}']
        }

        edge_head_type = 'Note'
        edge_head_query = {
            'invitation' : self.conference.get_blind_submission_id()
        }
        edge_weight={
            'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
        }
        edge_label={
            'value-regex': '.*'
        }
        if self.conference.get_custom_max_papers_id(self.match_group.id) == edge_id:
            edge_head_type = 'Group'
            edge_head_query = {
                'id' : edge_id.split('/-/')[0]
            }
            edge_weight={
                'value-dropdown': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15],
                'required': True
            }
            edge_label=None
        if self.alternate_matching_group:
            edge_head_type = 'Profile'
            edge_head_query = {
                'group' : self.alternate_matching_group
            }
            readers = {
                'values-copied': edge_readers + ['{tail}', '{head}']
            }

        edge_tail={
            'type': 'Profile',
            'query' : {
                'group' : self.match_group.id
            }
        }

        if any_tail:
            edge_tail['query'] = {
                'value-regex': '~.*|.+@.+'
            }
            edge_tail['description'] = 'Enter a valid email address or profile ID'
            edge_writers = [self.conference.get_id()]

        if default_label:
            edge_label['default']=default_label

        content={
            'head': {
                'type': edge_head_type,
                'query' : edge_head_query
            },
            'tail': edge_tail,
            'weight': edge_weight
        }

        if edge_label:
            content['label']=edge_label

        invitation = openreview.Invitation(
            id=edge_id,
            invitees=edge_invitees,
            readers=invitation_readers,
            writers=[self.conference.get_id()],
            signatures=[self.conference.get_id()],
            reply={
                'readers': readers,
                'nonreaders': edge_nonreaders,
                'writers': {
                    'values': edge_writers
                },
                'signatures': {
                    'values-regex': '|'.join(edge_signatures),
                    'default': self.conference.get_program_chairs_id()
                },
                'content': content
            })

        invitation = self.client.post_invitation(invitation)
        return invitation

    def _build_conflicts(self, submissions, user_profiles, get_profile_info, compute_conflicts_n_years):
        if self.alternate_matching_group:
            other_matching_group = self.client.get_group(self.alternate_matching_group)
            other_matching_profiles = tools.get_profiles(self.client, other_matching_group.members)
            return self._build_profile_conflicts(other_matching_profiles, user_profiles)
        return self._build_note_conflicts(submissions, user_profiles, get_profile_info, compute_conflicts_n_years)

    def append_note_conflicts(self, profile_id, build_conflicts=None):
        '''
        Create conflict edges between the given Notes and a single profile
        '''

        # Adapt single profile to multi-profile code
        user_profiles = [profile_id]
        user_profiles = tools.get_profiles(self.client, user_profiles, with_publications=build_conflicts)
        # Check for existing OpenReview profile - perform dummy check
        if user_profiles[0].active == None:
            raise openreview.OpenReviewException('No profile exists')
        get_profile_info = openreview.tools.get_neurips_profile_info if build_conflicts == 'NeurIPS' else openreview.tools.get_profile_info
        info_function = openreview.tools.info_function_builder(get_profile_info)
        user_profiles_info = [info_function(p) for p in user_profiles]

        # Re-setup information that would have been initialized in setup()
        submissions = self.conference.client.get_all_notes(
            invitation=self.conference.get_blind_submission_id(),
            details='original')

        # Fetch conflict invitation
        try:
            invitation = self.client.get_invitation(self.conference.get_conflict_score_id(self.match_group.id))
        except:
            raise openreview.OpenReviewException('Failed to retrieve conflict invitation')

        edges = []

        # Redo submission-author-user loop from _build_note_conflicts
        for submission in tqdm(submissions, total=len(submissions), desc='_build_conflicts'):
            # Get author profiles
            authorids = submission.content['authorids']
            if submission.details and submission.details.get('original'):
                authorids = submission.details['original']['content']['authorids']

            # Extract domains from each profile
            author_profiles = tools.get_profiles(self.client, authorids, with_publications=True)
            author_domains = set()
            author_emails = set()
            author_relations = set()
            author_publications = set()

            for author_profile in author_profiles:
                author_info = info_function(author_profile)
                author_domains.update(author_info['domains'])
                author_emails.update(author_info['emails'])
                author_relations.update(author_info['relations'])
                author_publications.update(author_info['publications'])

            # Compute conflicts for the user and all the paper authors
            for user_info in user_profiles_info:
                conflicts = set()
                conflicts.update(author_domains.intersection(user_info['domains']))
                conflicts.update(author_relations.intersection(user_info['emails']))
                conflicts.update(author_emails.intersection(user_info['relations']))
                conflicts.update(author_emails.intersection(user_info['emails']))
                conflicts.update(author_publications.intersection(user_info['publications']))

                if conflicts:
                    edges.append(Edge(
                        invitation=invitation.id,
                        head=submission.id,
                        tail=user_info['id'],
                        weight=-1,
                        label='Conflict',
                        readers=self._get_edge_readers(tail=user_info['id']),
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))

        ## Delete any previous conflicts related to single user
        self.client.delete_edges(invitation.id, tail=user_info['id'], wait_to_finish=True)

        original_edges_posted = self.client.get_edges_count(invitation=invitation.id)
        openreview.tools.post_bulk_edges(client=self.client, edges=edges)

        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation.id)
        intended_edges_posted = original_edges_posted + len(edges)
        if intended_edges_posted < edges_posted:
            raise openreview.OpenReviewException('Failed during bulk post of Conflict edges! Conflicts found: {0}, Edges posted: {1}'.format(intended_edges_posted, edges_posted))
        return invitation


    def _build_note_conflicts(self, submissions, user_profiles, get_profile_info, compute_conflicts_n_years=None):
        '''
        Create conflict edges between the given Notes and Profiles
        '''
        info_function = tools.info_function_builder(get_profile_info)
        invitation = self._create_edge_invitation(self.conference.get_conflict_score_id(self.match_group.id))
        # Get profile info from the match group
        user_profiles_info = [info_function(p, compute_conflicts_n_years) for p in user_profiles]
        # Get profile info from all the authors
        all_authorids = []
        for submission in submissions:
            authorids = submission.content['authorids']
            if submission.details and submission.details.get('original'):
                authorids = submission.details['original']['content']['authorids']
            all_authorids = all_authorids + authorids

        author_profile_by_id = tools.get_profiles(self.client, list(set(all_authorids)), with_publications=True, as_dict=True)

        edges = []

        for submission in tqdm(submissions, total=len(submissions), desc='_build_conflicts'):
            # Get author profiles
            authorids = submission.content['authorids']
            if submission.details and submission.details.get('original'):
                authorids = submission.details['original']['content']['authorids']

            # Extract domains from each autyhorprofile
            author_domains = set()
            author_emails = set()
            author_relations = set()
            author_publications = set()
            for authorid in authorids:
                if author_profile_by_id.get(authorid):
                    author_info = info_function(author_profile_by_id[authorid], compute_conflicts_n_years)
                    author_domains.update(author_info['domains'])
                    author_emails.update(author_info['emails'])
                    author_relations.update(author_info['relations'])
                    author_publications.update(author_info['publications'])
                else:
                    print(f'Profile not found: {authorid}')

            # Compute conflicts for each user and all the paper authors
            for user_info in user_profiles_info:
                conflicts = set()
                conflicts.update(author_domains.intersection(user_info['domains']))
                conflicts.update(author_relations.intersection(user_info['emails']))
                conflicts.update(author_emails.intersection(user_info['relations']))
                conflicts.update(author_emails.intersection(user_info['emails']))
                conflicts.update(author_publications.intersection(user_info['publications']))

                if conflicts:
                    edges.append(Edge(
                        invitation=invitation.id,
                        head=submission.id,
                        tail=user_info['id'],
                        weight=-1,
                        label='Conflict',
                        readers=self._get_edge_readers(tail=user_info['id']),
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))

        ## Delete previous conflicts
        self.client.delete_edges(invitation.id, wait_to_finish=True)

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)

        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation.id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of Conflict edges! Scores found: {0}, Edges posted: {1}'.format(len(edges), edges_posted))
        return invitation

    def _build_profile_conflicts(self, head_profiles, user_profiles):
        '''
        Create conflict edges between the given Profiles and Profiles
        '''
        invitation = self._create_edge_invitation(self.conference.get_conflict_score_id(self.match_group.id))
        # Get profile info from the match group
        info_function = openreview.tools.info_function_builder(openreview.tools.get_profile_info)
        user_profiles_info = [info_function(p) for p in user_profiles]
        head_profiles_info = [info_function(p) for p in head_profiles]

        edges = []

        for head_profile_info in tqdm(head_profiles_info, total=len(head_profiles_info), desc='_build_profile_conflicts'):

            # Compute conflicts for each user and all the paper authors
            for user_info in user_profiles_info:
                conflicts = set()
                conflicts.update(head_profile_info['domains'].intersection(user_info['domains']))
                conflicts.update(head_profile_info['relations'].intersection(user_info['emails']))
                conflicts.update(head_profile_info['emails'].intersection(user_info['relations']))
                conflicts.update(head_profile_info['emails'].intersection(user_info['emails']))
                if conflicts:
                    edges.append(Edge(
                        invitation=invitation.id,
                        head=head_profile_info['id'],
                        tail=user_info['id'],
                        weight=-1,
                        label='Conflict',
                        readers=self._get_edge_readers(tail=user_info['id']),
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))

        ## Delete previous conflicts
        self.client.delete_edges(invitation.id, wait_to_finish=True)

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)

        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation.id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of Conflict edges! Scores found: {0}, Edges posted: {1}'.format(len(edges), edges_posted))
        return invitation

    def _build_tpms_scores(self, tpms_score_file, submissions, user_profiles):
        '''
        Create tpms score edges given a csv file with scores, papers, and profiles.
        '''
        # pylint: disable=too-many-locals
        invitation = self._create_edge_invitation(self._get_edge_invitation_id('TPMS_Score'))

        submissions_per_number = {note.number: note for note in submissions}
        profiles_by_email = {}
        for profile in user_profiles:
            for email in profile.content['emails']:
                profiles_by_email[email] = profile

        edges = []
        with open(tpms_score_file) as file_handle:
            for row in tqdm(csv.reader(file_handle), desc='_build_tpms_scores'):
                number = int(row[0])
                score = row[2]
                if number in submissions_per_number and re.match(r'^-?\d+(?:\.\d+)?$', score):
                    paper_note_id = submissions_per_number[number].id
                    profile = profiles_by_email.get(row[1])
                    if profile:
                        profile_id = profile.id
                    else:
                        profile_id = row[1]

                    edges.append(Edge(
                        invitation=invitation.id,
                        head=paper_note_id,
                        tail=profile_id,
                        weight=float(score),
                        readers=self._get_edge_readers(tail=profile_id),
                        nonreaders=[self.conference.get_authors_id(number=number)],
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))

        ## Delete previous scores
        self.client.delete_edges(invitation.id, wait_to_finish=True)

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)
        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation.id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of TPMS edges! Input file:{0}, Scores found: {1}, Edges posted: {2}'.format(tpms_score_file, len(edges), edges_posted))
        return invitation

    def _build_scores_from_file(self, score_invitation_id, score_file, submissions):
        if self.alternate_matching_group:
            return self._build_profile_scores(score_invitation_id, score_file)
        scores = []
        with open(score_file) as file_handle:
            scores = [row for row in csv.reader(file_handle)]
        return self._build_note_scores(score_invitation_id, scores, submissions)

    def _build_scores_from_stream(self, score_invitation_id, scores_stream, submissions):
        scores = [input_line.split(',') for input_line in scores_stream.decode().split('\n')]
        return self._build_note_scores(score_invitation_id, scores, submissions)

    def _build_note_scores(self, score_invitation_id, scores, submissions):
        '''
        Given an array of scores and submissions, create score edges
        '''
        invitation = self._create_edge_invitation(score_invitation_id)

        submissions_per_id = {note.id: note.number for note in submissions}

        edges = []
        deleted_papers = set()
        for score_line in tqdm(scores, desc='_build_scores'):
            if score_line:
                paper_note_id = score_line[0]
                paper_number = submissions_per_id.get(paper_note_id)
                if paper_number:
                    profile_id = score_line[1]
                    score = str(max(round(float(score_line[2]), 4), 0))
                    edges.append(openreview.Edge(
                        invitation=invitation.id,
                        head=paper_note_id,
                        tail=profile_id,
                        weight=float(score),
                        readers=self._get_edge_readers(tail=profile_id),
                        nonreaders=[self.conference.get_authors_id(number=paper_number)],
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))
                else:
                    deleted_papers.add(paper_note_id)

        print('deleted papers', deleted_papers)

        ## Delete previous scores
        self.client.delete_edges(invitation.id, wait_to_finish=True)

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)
        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation.id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of {0} edges! Input file:{1}, Scores found: {2}, Edges posted: {3}'.format(score_invitation_id, score_file, len(edges), edges_posted))
        return invitation

    def _build_profile_scores(self, score_invitation_id, score_file = None, scores = None):
        '''
        Given a csv file or score list with affinity scores, create score edges
        '''
        invitation = self._create_edge_invitation(score_invitation_id)
        edges = []

        # Validate and select scores
        if not scores and not score_file:
            raise openreview.OpenReviewException('No profile scores provided')
        if scores:
            score_handle = scores
        elif score_file:
            score_handle = csv.reader(open(score_file))

        for row in tqdm(score_handle, desc='_build_scores'):
            edges.append(Edge(
                invitation=invitation.id,
                head=row[0],
                tail=row[1],
                weight=str(max(round(float(row[2]), 4), 0)),
                readers=self._get_edge_readers(tail=row[1]),
                writers=[self.conference.id],
                signatures=[self.conference.id]
            ))

        ## Delete previous scores
        self.client.delete_edges(invitation.id, wait_to_finish=True)

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)
        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation.id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of {0} edges! Input file:{1}, Scores found: {2}, Edges posted: {3}'.format(score_invitation_id, score_file, len(edges), edges_posted))
        return invitation

    def _build_subject_area_scores(self, submissions):
        '''
        Create subject area scores between all users in the match group and all given submissions
        '''
        invitation = self._create_edge_invitation(self._get_edge_invitation_id('Subject_Areas_Score'))

        edges = []
        user_subject_areas = self.client.get_all_notes(invitation=self.conference.get_registration_id(self.match_group.id))

        for note in tqdm(submissions, total=len(submissions), desc='_build_subject_area_scores'):
            note_subject_areas = note.content['subject_areas']
            paper_note_id = note.id
            for subject_area_note in user_subject_areas:
                profile_id = subject_area_note.signatures[0]
                if profile_id in self.match_group.members:
                    subject_areas = subject_area_note.content['subject_areas']
                    score = _jaccard_similarity(note_subject_areas, subject_areas)
                    edges.append(Edge(
                        invitation=invitation.id,
                        head=paper_note_id,
                        tail=profile_id,
                        weight=float(score),
                        readers=self._get_edge_readers(tail=profile_id),
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))

        ## Delete previous scores
        self.client.delete_edges(invitation.id, wait_to_finish=True)

        print('post edges', edges)
        openreview.tools.post_bulk_edges(client=self.conference.client, edges=edges)
        # Perform sanity check
        edges_posted = self.conference.client.get_edges_count(invitation=invitation.id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of edges! Scores found: {0}, Edges posted: {1}'.format(len(edges), edges_posted))
        return invitation

    def _compute_scores(self, score_invitation_id, submissions, model='specter+mfr'):

        matching_status = {
            'no_profiles': [],
            'no_publications': []
        }

        try:
            job_id = self.client.request_expertise(
                name=self.conference.get_short_name(),
                group_id=self.match_group.id,
                paper_invitation=self.conference.get_blind_submission_id(),
                alternate_match_group = self.alternate_matching_group,
                exclusion_inv=self.conference.get_expertise_selection_id(),
                model=model)
            status = ''
            call_count = 0
            while 'Completed' not in status and 'Error' not in status:
                if call_count == 1440: ## one day to wait the completion or trigger a timeout
                    break
                time.sleep(60)
                status_response = self.client.get_expertise_status(job_id['jobId'])
                status = status_response.get('status')
                desc = status_response.get('description')
                call_count += 1
            if 'Completed' in status:
                result = self.client.get_expertise_results(job_id['jobId'])
                matching_status['no_profiles'] = result['metadata']['no_profile']
                matching_status['no_publications'] = result['metadata']['no_publications']

                if self.alternate_matching_group:
                    scores = [[entry['submission_member'], entry['match_member'], entry['score']] for entry in result['results']]
                    return self._build_profile_scores(score_invitation_id, scores=scores), matching_status

                scores = [[entry['submission'], entry['user'], entry['score']] for entry in result['results']]
                return self._build_note_scores(score_invitation_id, scores, submissions), matching_status
            if 'Error' in status:
                raise openreview.OpenReviewException('There was an error computing scores, description: ' + desc)
            if call_count == 1440:
                raise openreview.OpenReviewException('Time out computing scores, description: ' + desc)
        except openreview.OpenReviewException as e:
            raise openreview.OpenReviewException('There was an error connecting with the expertise API: ' + str(e))

    def _build_custom_max_papers(self, user_profiles):
        invitation=self._create_edge_invitation(self.conference.get_custom_max_papers_id(self.match_group.id))
        current_custom_max_edges={ e['id']['tail']: Edge.from_json(e['values'][0]) for e in self.client.get_grouped_edges(invitation=invitation.id, groupby='tail', select=None)}

        reduced_loads = {}
        if self.conference.use_recruitment_template:
            reduced_load_notes = self.client.get_all_notes(invitation=self.conference.get_recruitment_id(self.match_group.id), sort='tcdate:asc')
            for note in tqdm(reduced_load_notes, desc='getting reduced load notes'):
                reduced_loads[note.content['user']] = note.content.get('reduced_load')
        else:
            reduced_load_notes = self.client.get_all_notes(invitation=self.conference.get_invitation_id('Reduced_Load', prefix = self.match_group.id), sort='tcdate:asc')
            for note in tqdm(reduced_load_notes, desc='getting reduced load notes'):
                reduced_loads[note.content['user']] = note.content['reviewer_load']

        print ('Reduced loads received: ', len(reduced_loads))

        edges = []
        for user_profile in tqdm(user_profiles):

            custom_load = None
            ids = user_profile.content['emailsConfirmed'] + [ n['username'] for n in user_profile.content['names'] if 'username' in n]
            for i in ids:
                if not custom_load and (i in reduced_loads):
                    custom_load = reduced_loads[i]

            if custom_load:
                current_edge = current_custom_max_edges.get(user_profile.id)
                review_capacity = int(custom_load)

                if current_edge:
                    ## Update edge if the new capacity is lower
                    if current_edge.weight > review_capacity:
                        print(f'Update edge for {user_profile.id}')
                        current_edge.weight=review_capacity
                        self.client.post_edge(current_edge)

                else:
                    edge = Edge(
                        head=self.match_group.id,
                        tail=user_profile.id,
                        invitation=invitation.id,
                        readers=self._get_edge_readers(user_profile.id),
                        writers=[self.conference.id],
                        signatures=[self.conference.id],
                        weight=review_capacity
                    )
                    edges.append(edge)


        openreview.tools.post_bulk_edges(client=self.client, edges=edges)

        return invitation

    def _build_config_invitation(self, scores_specification):
        '''
        Builds an assignment configuration invitation that specifies the match
        between papers and this Matching's match group
        '''
        config_inv = openreview.Invitation(
            id='{}/-/{}'.format(self.match_group.id, 'Assignment_Configuration'),
            invitees=[self.conference.get_id(), self.conference.support_user],
            readers=[self.conference.get_id()],
            writers=[self.conference.get_id()],
            signatures=[self.conference.get_id()],
            reply={
                'forum': None,
                'replyto': None,
                'invitation': None,
                'readers': {'values': [self.conference.get_id()]},
                'writers': {'values': [self.conference.get_id()]},
                'signatures': {'values': [self.conference.get_id()]},
                'content': {
                    'title': {
                        'value-regex': '^[a-zA-Z0-9-_][a-zA-Z0-9-_ ]{1,250}$',
                        'required': True,
                        'description': 'Title of the configuration. Only alphanumeric characters, dashes and underscores are allowed.',
                        'order': 1
                    },
                    'user_demand': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Number of users that can review a paper',
                        'order': 2
                    },
                    'max_papers': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Max number of reviews a user has to do',
                        'order': 3
                    },
                    'min_papers': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Min number of reviews a user should do',
                        'order': 4
                    },
                    'alternates': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'The number of alternate reviewers to save (per-paper)',
                        'order': 5
                    },
                    'paper_invitation': {
                        'value-regex': self.alternate_matching_group if self.alternate_matching_group else self.conference.get_blind_submission_id() + '.*',
                        'default': self.alternate_matching_group if self.alternate_matching_group else self.conference.get_blind_submission_id(),
                        'required': True,
                        'description': 'Invitation to get the paper metadata or Group id to get the users to be matched',
                        'order': 6
                    },
                    'match_group': {
                        'value-regex': '{}/.*'.format(self.conference.id),
                        'default': self.match_group.id,
                        'required': True,
                        'description': 'Group id containing users to be matched',
                        'order': 7
                    },
                    'scores_specification': {
                        'value-dict': {},
                        'required': False,
                        'description': 'Manually entered JSON score specification',
                        'order': 8,
                        'default': scores_specification
                    },
                    'aggregate_score_invitation': {
                        'value-regex': '{}/.*'.format(self.conference.id),
                        'default': self._get_edge_invitation_id('Aggregate_Score'),
                        'required': True,
                        'description': 'Invitation to store aggregated scores',
                        'order': 9,
                        'hidden': True
                    },
                    'conflicts_invitation': {
                        'value-regex': '{}/.*'.format(self.conference.id),
                        'default': self.conference.get_conflict_score_id(self.match_group.id),
                        'required': True,
                        'description': 'Invitation to store conflict scores',
                        'order': 10
                    },
                    'assignment_invitation': {
                        'value': self.conference.get_paper_assignment_id(self.match_group.id),
                        'required': True,
                        'description': 'Invitation to store paper user assignments',
                        'order': 11,
                        'hidden': True
                    },
                    'deployed_assignment_invitation': {
                        'value': self.conference.get_paper_assignment_id(self.match_group.id, deployed=True),
                        'required': True,
                        'description': 'Invitation to store deployed paper user assignments',
                        'order': 12,
                        'hidden': True
                    },
                    'invite_assignment_invitation': {
                        'value': self.conference.get_paper_assignment_id(self.match_group.id, invite=True),
                        'required': True,
                        'description': 'Invitation used to invite external or emergency reviewers',
                        'order': 13,
                        'hidden': True
                    },
                    'custom_user_demand_invitation': {
                        'value-regex': '{}/.*/-/Custom_User_Demands$'.format(self.conference.id),
                        'default': '{}/-/Custom_User_Demands'.format(self.match_group.id),
                        'description': 'Invitation to store custom number of users required by papers',
                        'order': 14,
                        'required': False
                    },
                    'custom_max_papers_invitation': {
                        'value-regex': '{}/.*/-/Custom_Max_Papers$'.format(self.conference.id),
                        'default': self.conference.get_custom_max_papers_id(self.match_group.id),
                        'description': "Invitation to store custom max number of papers that can be assigned to reviewers",
                        'order': 15,
                        'required': False
                    },
                    'config_invitation': {
                        'value': self._get_edge_invitation_id('Assignment_Configuration'),
                        'order': 16,
                        'hidden': True
                    },
                    'solver': {
                        'value-radio': ['MinMax', 'FairFlow', 'Randomized', 'FairSequence'],
                        'default': 'MinMax',
                        'required': True,
                        'order': 17
                    },
                    'status': {
                        'default': 'Initialized',
                        'value-dropdown': [
                            'Initialized',
                            'Running',
                            'Error',
                            'No Solution',
                            'Complete',
                            'Deploying',
                            'Deployed',
                            'Deployment Error',
                            'Queued',
                            'Cancelled'
                        ],
                        'order': 18
                    },
                    'error_message': {
                        'value-regex': '.*',
                        'required': False,
                        'order': 18,
                        'hidden': True
                    },
                    'allow_zero_score_assignments': {
                        'description': 'Select "No" only if you do not want to allow assignments with 0 scores. Note that if there are any users without publications, you need to select "Yes" in order to run a paper matching.',
                        'value-radio': ['Yes', 'No'],
                        'required': False,
                        'default': 'Yes',
                        'order': 20
                    },
                    'randomized_probability_limits': {
                        'description': 'Enter the probability limits if the selected solver is Randomized',
                        'value-regex': r'[-+]?[0-9]*\.?[0-9]*',
                        'required': False,
                        'default': '1',
                        'order': 21
                    },
                    'randomized_fraction_of_opt': {
                        'description': 'result of randomized assignment',
                        'value-regex': r'[-+]?[0-9]*\.?[0-9]*',
                        'required': False,
                        'default': '',
                        'order': 22,
                        'hidden': True
                    }
                }
            })
        self.client.post_invitation(config_inv)

    def compute_alternate_conflicts(self, assignment_title, conflict_label='Conflict', build_conflicts='NeurIPS'):
        if not self.alternate_matching_group:
            raise openreview.OpenReviewException('No alternate group selected')

        ## Compute conflicts for the matching group
        submissions = self.conference.client.get_all_notes(invitation=self.conference.get_blind_submission_id(), details='original')
        user_profiles = tools.get_profiles(self.client, self.match_group.members, with_publications=build_conflicts)
        self._build_note_conflicts(submissions, user_profiles, openreview.tools.get_neurips_profile_info if build_conflicts == 'NeurIPS' else openreview.tools.get_profile_info)

        ## Get proposed assignments and conflicts from both groups: match and alternate groups
        proposed_assignment_edges =  { e['id']['head']: [v['tail'] for v in e['values']][0] for e in self.client.get_grouped_edges(invitation=self.conference.get_paper_assignment_id(self.match_group.id),
            label=assignment_title, groupby='head', select='tail')}
        match_group_conflict_edges =  { e['id']['head']: [v['tail'] for v in e['values']] for e in self.client.get_grouped_edges(invitation=self.conference.get_conflict_score_id(self.match_group.id), groupby='head', select='tail')}
        alternate_group_conflict_edges =  { e['id']['head']: [v['tail'] for v in e['values']] for e in self.client.get_grouped_edges(invitation=self.conference.get_conflict_score_id(self.alternate_matching_group), groupby='head', select='tail')}
        alternate_group_members = self.client.get_group(self.alternate_matching_group).members

        edges = []

        for submission in tqdm(submissions, total=len(submissions), desc='compute_alternate_conflicts'):
            submission_alternate_group_conflicts = alternate_group_conflict_edges.get(submission.id, [])
            submission_match_group_conflicts = match_group_conflict_edges.get(submission.id, [])
            for member in alternate_group_members:       
                if member not in submission_alternate_group_conflicts:
                    assigned_match_group = proposed_assignment_edges[member]
                    if assigned_match_group in submission_match_group_conflicts:
                        edges.append(Edge(
                        invitation=self.conference.get_conflict_score_id(self.alternate_matching_group),
                        head=submission.id,
                        tail=member,
                        weight=-1,
                        label=conflict_label,
                        readers=self._get_edge_readers(tail=member),
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)
        print(f'Poster {len(edges)} alternate conflict edges')
    
    
    def setup(self, compute_affinity_scores=False, tpms_score_file=None, elmo_score_file=None, build_conflicts=None, compute_conflicts_n_years=None):
        '''
        Build all the invitations and edges necessary to run a match
        '''
        score_spec = {}
        matching_status = {
            'no_profiles': [],
            'no_publications': []
        }

        try:
            invitation = self.client.get_invitation(self.conference.get_bid_id(self.match_group.id))
            score_spec[invitation.id] = {
                'weight': 1,
                'default': 0,
                'translate_map' : {
                    'Very High': 1.0,
                    'High': 0.5,
                    'Neutral': 0.0,
                    'Low': -0.5,
                    'Very Low': -1.0
                }
            }
        except:
            print('Bid invitation not found')

        try:
            invitation = self.client.get_invitation(self.conference.get_recommendation_id())
            score_spec[invitation.id] = {
                'weight': 1,
                'default': 0
            }
        except:
            print('Recommendation invitation not found')

        # The reviewers are all emails so convert to tilde ids
        self.match_group = openreview.tools.replace_members_with_ids(self.client, self.match_group)
        matching_status['no_profiles'] = [member for member in self.match_group.members if '~' not in member]
        if matching_status['no_profiles']:
            print(
                'WARNING: not all reviewers have been converted to profile IDs.',
                'Members without profiles will not have metadata created.')

        user_profiles = tools.get_profiles(self.client, self.match_group.members, with_publications=build_conflicts)

        invitation = self._create_edge_invitation(self.conference.get_paper_assignment_id(self.match_group.id))
        if not self.is_senior_area_chair:
            with open(os.path.join(os.path.dirname(__file__), 'templates/proposed_assignment_pre_process.py')) as f:
                content = f.read()
                content = content.replace("CUSTOM_MAX_PAPERS_INVITATION_ID = ''", "CUSTOM_MAX_PAPERS_INVITATION_ID = '" + self.conference.get_custom_max_papers_id(self.match_group.id) + "'")
                invitation.preprocess=content
                self.client.post_invitation(invitation)

        self._create_edge_invitation(self.conference.get_paper_assignment_id(self.match_group.id, deployed=True))
        self.conference.invitation_builder.set_assignment_invitation(self.conference, self.match_group.id)
        self._create_edge_invitation(self._get_edge_invitation_id('Aggregate_Score'))
        self._build_custom_max_papers(user_profiles)
        self._create_edge_invitation(self._get_edge_invitation_id('Custom_User_Demands'))

        submissions = self.conference.client.get_all_notes(invitation=self.conference.get_blind_submission_id(), details='original')

        if not self.match_group.members:
            raise openreview.OpenReviewException(f'The match group is empty: {self.match_group.id}')
        if self.alternate_matching_group:
            other_matching_group = self.client.get_group(self.alternate_matching_group)
            if not other_matching_group.members:
                raise openreview.OpenReviewException(f'The alternate match group is empty: {self.alternate_matching_group}')
        elif not submissions:
            raise openreview.OpenReviewException('Submissions not found.')

        if tpms_score_file:
            invitation = self._build_tpms_scores(tpms_score_file, submissions, user_profiles)
            score_spec[invitation.id] = {
                'weight': 1,
                'default': 0
            }

        type_affinity_scores = type(compute_affinity_scores)

        if type_affinity_scores == str:
            if compute_affinity_scores in ['specter+mfr', 'specter2', 'scincl', 'specter2+scincl']:
                invitation, matching_status = self._compute_scores(
                    self.conference.get_affinity_score_id(self.match_group.id),
                    submissions,
                    compute_affinity_scores
                )
            else:             
                invitation = self._build_scores_from_file(
                    self.conference.get_affinity_score_id(self.match_group.id),
                    compute_affinity_scores,
                    submissions
                )
            score_spec[invitation.id] = {
                'weight': 1,
                'default': 0
            }

        if type_affinity_scores == bytes:
            invitation = self._build_scores_from_stream(
                self.conference.get_affinity_score_id(self.match_group.id),
                compute_affinity_scores,
                submissions
            )
            if invitation:
                score_spec[invitation.id] = {
                    'weight': 1,
                    'default': 0
                }

        if elmo_score_file:
            invitation = self._build_scores_from_file(
                self.conference.get_elmo_score_id(self.match_group.id),
                elmo_score_file,
                submissions
            )
            score_spec[invitation.id] = {
                'weight': 1,
                'default': 0
            }

        if self.conference.submission_stage.subject_areas:
            invitation = self._build_subject_area_scores(submissions)
            score_spec[invitation.id] = {
                'weight': 1,
                'default': 0
            }

        if compute_affinity_scores == True:
            invitation, matching_status = self._compute_scores(
                self.conference.get_affinity_score_id(self.match_group.id),
                submissions
            )
            if invitation:
                score_spec[invitation.id] = {
                    'weight': 1,
                    'default': 0
                }

        if build_conflicts:
            self._build_conflicts(submissions, user_profiles, openreview.tools.get_neurips_profile_info if build_conflicts == 'NeurIPS' else openreview.tools.get_profile_info, compute_conflicts_n_years)

        self._build_config_invitation(score_spec)
        return matching_status

    def setup_invite_assignment(self, hash_seed, assignment_title=None, due_date=None, invitation_labels={}, invited_committee_name='External_Reviewers', email_template=None, proposed=False):

        invite_label=invitation_labels.get('Invite', 'Invitation Sent')
        invited_label=invitation_labels.get('Invited', 'Invitation Sent')
        accepted_label=invitation_labels.get('Accepted', 'Accepted')
        declined_label=invitation_labels.get('Declined', 'Declined')

        recruitment_invitation_id=self.conference.get_invitation_id('Proposed_Assignment_Recruitment' if assignment_title else 'Assignment_Recruitment', prefix=self.match_group.id)

        invitation=self._create_edge_invitation(self.conference.get_paper_assignment_id(self.match_group.id, invite=True), any_tail=True, default_label=invite_label)
        with open(os.path.join(os.path.dirname(__file__), 'templates/invite_assignment_pre_process.py')) as pre:
            with open(os.path.join(os.path.dirname(__file__), 'templates/invite_assignment_post_process.py')) as post:
                pre_content = pre.read()
                post_content = post.read()
                pre_content = pre_content.replace("REVIEWERS_ID = ''", "REVIEWERS_ID = '" + self.match_group.id + "'")
                post_content = post_content.replace("SHORT_PHRASE = ''", f'SHORT_PHRASE = "{self.conference.get_short_name()}"')
                post_content = post_content.replace("RECRUITMENT_INVITATION_ID = ''", "RECRUITMENT_INVITATION_ID = '" + recruitment_invitation_id + "'")
                post_content = post_content.replace("REVIEWERS_INVITED_ID = ''", "REVIEWERS_INVITED_ID = '" + self.conference.get_committee_id(name=invited_committee_name + '/Invited')  + "'")
                if email_template:
                    post_content = post_content.replace("EMAIL_TEMPLATE = ''", "EMAIL_TEMPLATE = '''" + email_template  + "'''")
                if assignment_title:
                    pre_content = pre_content.replace("ASSIGNMENT_INVITATION_ID = ''", "ASSIGNMENT_INVITATION_ID = '" + self.conference.get_paper_assignment_id(self.match_group.id) + "'")
                    pre_content = pre_content.replace("ASSIGNMENT_LABEL = None", "ASSIGNMENT_LABEL = '" + assignment_title + "'")
                    post_content = post_content.replace("ASSIGNMENT_INVITATION_ID = ''", "ASSIGNMENT_INVITATION_ID = '" + self.conference.get_paper_assignment_id(self.match_group.id) + "'")
                    post_content = post_content.replace("ASSIGNMENT_LABEL = None", "ASSIGNMENT_LABEL = '" + assignment_title + "'")
                    post_content = post_content.replace("PAPER_REVIEWER_INVITED_ID = ''", "PAPER_REVIEWER_INVITED_ID = '" + self.conference.get_committee_id(name=invited_committee_name + '/Invited', number='{number}')  + "'")
                else:
                    pre_content = pre_content.replace("ASSIGNMENT_INVITATION_ID = ''", "ASSIGNMENT_INVITATION_ID = '" + self.conference.get_paper_assignment_id(self.match_group.id, deployed=True) + "'")
                    post_content = post_content.replace("ASSIGNMENT_INVITATION_ID = ''", "ASSIGNMENT_INVITATION_ID = '" + self.conference.get_paper_assignment_id(self.match_group.id, deployed=True) + "'")

                post_content = post_content.replace("HASH_SEED = ''", "HASH_SEED = '" + hash_seed + "'")
                post_content = post_content.replace("INVITED_LABEL = ''", "INVITED_LABEL = '" + invited_label + "'")
                pre_content = pre_content.replace("INVITE_LABEL = ''", "INVITE_LABEL = '" + invite_label + "'")
                post_content = post_content.replace("INVITE_LABEL = ''", "INVITE_LABEL = '" + invite_label + "'")
                if self.conference.use_recruitment_template:
                    post_content = post_content.replace("USE_RECRUITMENT_TEMPLATE = False", "USE_RECRUITMENT_TEMPLATE = True")

                invitation.preprocess=pre_content
                invitation.process=post_content
                invitation.multiReply=False
                invitation.signatures=[self.conference.get_program_chairs_id()] ## Program Chairs have permission to see full profile data
                invite_assignment_invitation=self.client.post_invitation(invitation)

        invitation = self.conference.invitation_builder.set_paper_recruitment_invitation(self.conference,
            recruitment_invitation_id,
            self.match_group.id,
            invited_committee_name,
            hash_seed,
            assignment_title,
            due_date,
            invited_label=invited_label,
            accepted_label=accepted_label,
            declined_label=declined_label,
            proposed=proposed
        )
        invitation = self.conference.webfield_builder.set_paper_recruitment_page(self.conference, invitation)

        ## Only for reviewers, allow ACs and SACs to review the proposed assignments
        if self.match_group.id == self.conference.get_reviewers_id() and not proposed:
            self.conference.set_external_reviewer_recruitment_groups(name=invited_committee_name, create_paper_groups=True if assignment_title else False)
            if assignment_title:
                invitation=self.client.get_invitation(self.conference.get_paper_assignment_id(self.match_group.id))
                invitation.duedate=tools.datetime_millis(due_date)
                invitation.expdate=tools.datetime_millis(due_date + datetime.timedelta(minutes= 30)) if due_date else None
                invitation=self.client.post_invitation(invitation)
                invitation = self.conference.webfield_builder.set_reviewer_proposed_assignment_page(self.conference, invitation, assignment_title, invite_assignment_invitation)


        return invite_assignment_invitation


    def deploy_acs(self, assignment_title, overwrite):

        papers = self.client.get_all_notes(invitation=self.conference.get_blind_submission_id())
        reviews = self.client.get_notes(invitation=self.conference.get_invitation_id('Meta_Review', '.*'))
        assignment_edges =  { g['id']['head']: g['values'] for g in self.client.get_grouped_edges(invitation=self.conference.get_paper_assignment_id(self.match_group.id),
            label=assignment_title, groupby='head', select='tail')}

        if overwrite and reviews:
            raise openreview.OpenReviewException('Can not overwrite assignments when there are meta reviews posted.')

        for paper in tqdm(papers, total=len(papers)):
            ac_group = self.client.get_group('{conference_id}/Paper{number}/{name}'.format(conference_id=self.conference.id, number=paper.number, name=self.conference.area_chairs_name))

            if overwrite:
                ac_group.members = []
                self.client.post_group(ac_group)
                groups = self.client.get_groups(regex='{conference_id}/Paper{number}/Area_Chair[0-9]+'.format(conference_id=self.conference.id, number=paper.number))
                for group in groups:
                    self.client.delete_group(group.id)

            if paper.id in assignment_edges:

                ac_group_id = '{conference_id}/Paper{number}/{name}'.format(conference_id=self.conference.id, number=paper.number, name=self.conference.area_chairs_name)
                author_group = '{conference_id}/Paper{number}/Authors'.format(conference_id=self.conference.id, number=paper.number)
                members = [v['tail'] for v in assignment_edges[paper.id]]

                group = openreview.Group(id=ac_group_id,
                                        members=members,
                                        readers=[self.conference.id, ac_group_id],
                                        nonreaders=[author_group],
                                        signatories=[self.conference.id, ac_group_id],
                                        signatures=[self.conference.id],
                                        writers=[self.conference.id]
                                        )
                r = self.client.post_group(group)

                for index,member in enumerate(members):
                    anon_ac_group = '{conference_id}/Paper{number}/Area_Chair{index}'.format(conference_id=self.conference.id, number=paper.number, index=index+1)
                    group = openreview.Group(id=anon_ac_group,
                                            members=[member],
                                            readers=[self.conference.id, anon_ac_group],
                                            nonreaders=[author_group],
                                            signatories=[self.conference.id, anon_ac_group],
                                            signatures=[self.conference.id],
                                            writers=[self.conference.id]
                                            )
                    r = self.client.post_group(group)
            else:
                print('assignment not found', paper.id)

    def get_next_anon_id(self, start, end, prefix, anon_group_dict):
        for index in range(start, end):
            if prefix + str(index) not in anon_group_dict:
                return index
        return end

    def deploy_reviewers(self, assignment_title, overwrite):

        papers = self.client.get_all_notes(invitation=self.conference.get_blind_submission_id())
        reviews = self.client.get_notes(invitation=self.conference.get_invitation_id('Official_Review', '.*'))
        assignment_edges =  { g['id']['head']: g['values'] for g in self.client.get_grouped_edges(invitation=self.conference.get_paper_assignment_id(self.match_group.id),
            label=assignment_title, groupby='head', select='tail')}

        if overwrite and reviews:
            raise openreview.OpenReviewException('Can not overwrite assignments when there are reviews posted.')

        for paper in tqdm(papers, total=len(papers)):

            reviewers_group = self.client.get_group('{conference_id}/Paper{number}/{name}'.format(conference_id=self.conference.id, number=paper.number, name=self.conference.reviewers_name))
            anon_groups = self.client.get_groups(regex='{conference_id}/Paper{number}/AnonReviewer[0-9]+'.format(conference_id=self.conference.id, number=paper.number))
            anon_groups_dict = {}

            if overwrite:
                reviewers_group.members = []
                self.client.post_group(reviewers_group)
                for group in anon_groups:
                    self.client.delete_group(group.id)
            else:
                anon_groups_dict = { g.id: g for g in anon_groups if len(g.members) > 0 }

            if paper.id in assignment_edges:

                ac_group_id = '{conference_id}/Paper{number}/{name}'.format(conference_id=self.conference.id, number=paper.number, name=self.conference.area_chairs_name)
                reviewer_group_id = '{conference_id}/Paper{number}/{name}'.format(conference_id=self.conference.id, number=paper.number, name=self.conference.reviewers_name)
                author_group_id = '{conference_id}/Paper{number}/Authors'.format(conference_id=self.conference.id, number=paper.number)
                new_reviewers = [v['tail'] for v in assignment_edges[paper.id]]
                members = reviewers_group.members + new_reviewers

                group = openreview.Group(id=reviewer_group_id,
                                        members=members,
                                        readers=[self.conference.id, ac_group_id, reviewer_group_id],
                                        nonreaders=[author_group_id],
                                        signatories=[self.conference.id, ac_group_id],
                                        signatures=[self.conference.id],
                                        writers=[self.conference.id, ac_group_id]
                                        )
                r = self.client.post_group(group)

                number = 1
                for reviewer in new_reviewers:
                    prefix = '{conference_id}/Paper{number}/AnonReviewer'.format(conference_id=self.conference.id, number=paper.number)
                    number = self.get_next_anon_id(number, len(members), prefix, anon_groups_dict)
                    anon_reviewer_group_id = prefix + str(number)
                    number += 1

                    group = openreview.Group(id=anon_reviewer_group_id,
                                            members=[reviewer],
                                            readers=[self.conference.id, ac_group_id, anon_reviewer_group_id],
                                            nonreaders=[author_group_id],
                                            signatories=[self.conference.id, anon_reviewer_group_id],
                                            signatures=[self.conference.id],
                                            writers=[self.conference.id, ac_group_id]
                                            )
                    r = self.client.post_group(group)
            else:
                print('assignment not found', paper.id)

    def deploy_assignments(self, assignment_title, overwrite):

        committee_id=self.match_group.id
        role_name = committee_id.split('/')[-1]
        review_name = 'Official_Review'
        reviewer_name = self.conference.reviewers_name
        if role_name in self.conference.reviewer_roles:
            reviewer_name = self.conference.reviewers_name
            review_name = 'Official_Review'
        elif role_name in self.conference.area_chair_roles:
            reviewer_name = self.conference.area_chairs_name
            review_name = 'Meta_Review'

        papers = self.client.get_all_notes(invitation=self.conference.get_blind_submission_id(), details='directReplies')
        reviews = [reply for paper in papers for reply in paper.details['directReplies'] if review_name in reply['invitation']]
        proposed_assignment_edges =  { g['id']['head']: g['values'] for g in self.client.get_grouped_edges(invitation=self.conference.get_paper_assignment_id(self.match_group.id),
            label=assignment_title, groupby='head', select=None)}
        assignment_edges = []
        assignment_invitation_id = self.conference.get_paper_assignment_id(self.match_group.id, deployed=True)
        current_assignment_edges =  { g['id']['head']: g['values'] for g in self.client.get_grouped_edges(invitation=assignment_invitation_id, groupby='head', select=None)}

        if overwrite:
            if reviews:
                raise openreview.OpenReviewException('Can not overwrite assignments when there are reviews posted.')
            ## Remove the members from the groups based on the current assignments
            for paper in tqdm(papers, total=len(papers)):
                if paper.id in current_assignment_edges:
                    paper_committee_id = self.conference.get_committee_id(name=reviewer_name, number=paper.number)
                    current_edges=current_assignment_edges[paper.id]
                    for current_edge in current_edges:
                        self.client.remove_members_from_group(paper_committee_id, current_edge['tail'])
                else:
                    print('assignment not found', paper.id)
            ## Delete current assignment edges with a ddate in case we need to do rollback
            self.client.delete_edges(invitation=assignment_invitation_id, wait_to_finish=True, soft_delete=True)


        for paper in tqdm(papers, total=len(papers)):
            if paper.id in proposed_assignment_edges:
                paper_committee_id = self.conference.get_committee_id(name=reviewer_name, number=paper.number)
                proposed_edges=proposed_assignment_edges[paper.id]
                for proposed_edge in proposed_edges:
                    self.client.add_members_to_group(paper_committee_id, proposed_edge['tail'])
                    assignment_edges.append(Edge(
                        invitation=assignment_invitation_id,
                        head=paper.id,
                        tail=proposed_edge['tail'],
                        readers=proposed_edge['readers'],
                        nonreaders=proposed_edge['nonreaders'],
                        writers=proposed_edge['writers'],
                        signatures=proposed_edge['signatures'],
                        weight=proposed_edge.get('weight')
                    ))
            else:
                print('assignment not found', paper.id)

        print('POsting assignments edges', len(assignment_edges))
        openreview.tools.post_bulk_edges(client=self.client, edges=assignment_edges)

    def invite_proposed_assignments(self, assignment_title):

        papers = self.client.get_all_notes(invitation=self.conference.get_blind_submission_id())
        proposed_assignment_edges =  { g['id']['head']: g['values'] for g in self.client.get_grouped_edges(invitation=self.conference.get_paper_assignment_id(self.match_group.id),
            label=assignment_title, groupby='head', select=None)}
        invite_assignment_edges = []
        invite_assignment_invitation_id = self.conference.get_paper_assignment_id(self.match_group.id, invite=True)

        for paper in tqdm(papers, total=len(papers)):

            if paper.id in proposed_assignment_edges:
                proposed_edges=proposed_assignment_edges[paper.id]
                for proposed_edge in proposed_edges:
                    invite_edge=openreview.Edge(
                        invitation=invite_assignment_invitation_id,
                        head=proposed_edge['head'],
                        tail=proposed_edge['tail'],
                        label='Invitation Sent',
                        readers=proposed_edge['readers'],
                        nonreaders=proposed_edge['nonreaders'],
                        writers=[self.conference.id],
                        signatures=proposed_edge['signatures']
                    )
                    posted_edge=self.client.post_edge(invite_edge)
                    invite_assignment_edges.append(posted_edge)

            else:
                print('assignment not found', paper.id)

        print('Posted invite assignment edges', len(invite_assignment_edges))
        return invite_assignment_edges

    def deploy_sac_assignments(self, assignment_title, overwrite):

        print('deploy_sac_assignments', assignment_title)

        papers = self.client.get_all_notes(invitation=self.conference.get_blind_submission_id())

        proposed_assignment_edges =  { g['id']['head']: g['values'] for g in self.client.get_grouped_edges(invitation=self.conference.get_paper_assignment_id(self.match_group.id),
            label=assignment_title, groupby='head', select=None)}
        assignment_edges = []
        assignment_invitation_id = self.conference.get_paper_assignment_id(self.match_group.id, deployed=True)

        # Info for SAC-paper assignments
        paper_id_to_number = {p.id : p.number for p in papers}
        current_assignment_edges =  { g['id']['head']: g['values'] for g in self.client.get_grouped_edges(invitation=assignment_invitation_id, groupby='head', select=None)}
        reviewer_name = self.conference.senior_area_chairs_name
        assignment_invitation = self.client.get_invitation(assignment_invitation_id)
        are_paper_assignments = 'Profile' not in assignment_invitation.reply.get('content', {}).get('head', {}).get('type', 'Profile')

        ac_groups = {g.id:g for g in self.client.get_all_groups(regex=f'{self.conference.id}/Paper.*') if g.id.endswith(self.conference.area_chairs_name)}

        if not papers:
            raise openreview.OpenReviewException('No submissions to deploy SAC assignment')

        for paper in tqdm(papers):

            ac_group_id=self.conference.get_area_chairs_id(paper.number)

            ac_group=ac_groups.get(ac_group_id)

            if ac_group:
                if len(ac_group.members) == 0 and not are_paper_assignments:
                    raise openreview.OpenReviewException('AC assignments must be deployed first')

                for ac in ac_group.members:
                    sac_assignments = proposed_assignment_edges.get(ac, [])

                    for sac_assignment in sac_assignments:
                        sac=sac_assignment['tail']
                        sac_group_id=ac_group.id.replace(self.conference.area_chairs_name, self.conference.senior_area_chairs_name)
                        sac_group=self.client.get_group(sac_group_id)
                        if overwrite:
                            sac_group.members=[]
                        sac_group.members.append(sac)
                        self.client.post_group(sac_group)

            if overwrite and are_paper_assignments:
                if paper.id in current_assignment_edges:
                    paper_committee_id = self.conference.get_committee_id(name=reviewer_name, number=paper.number)
                    current_edges=current_assignment_edges[paper.id]
                    for current_edge in current_edges:
                        self.client.remove_members_from_group(paper_committee_id, current_edge['tail'])
                else:
                    print('assignment not found', paper.id)

        for head, sac_assignments in proposed_assignment_edges.items():
            for sac_assignment in sac_assignments:
                if are_paper_assignments:
                    paper_committee_id = self.conference.get_committee_id(name=reviewer_name, number=paper_id_to_number[head])
                    self.client.add_members_to_group(paper_committee_id, sac_assignment['tail'])
                assignment_edges.append(openreview.Edge(
                    invitation=assignment_invitation_id,
                    head=head,
                    tail=sac_assignment['tail'],
                    readers=sac_assignment['readers'],
                    nonreaders=sac_assignment['nonreaders'],
                    writers=sac_assignment['writers'],
                    signatures=sac_assignment['signatures'],
                    weight=sac_assignment.get('weight')
                ))

        print('Posting assignments edges', len(assignment_edges))
        openreview.tools.post_bulk_edges(client=self.client, edges=assignment_edges)


    def deploy(self, assignment_title, overwrite=False, enable_reviewer_reassignment=False):
        '''
        WARNING: This function untested

        '''

        ## Deploy assingments creating groups and assignment edges
        if self.match_group.id == self.conference.get_senior_area_chairs_id():
            self.deploy_sac_assignments(assignment_title, overwrite)
        else:
            self.deploy_assignments(assignment_title, overwrite)

        ## Add sync process function
        self.conference.invitation_builder.set_paper_group_invitation(self.conference, self.match_group.id)
        self.conference.invitation_builder.set_assignment_invitation(self.conference, self.match_group.id)

        if self.match_group.id == self.conference.get_reviewers_id() and enable_reviewer_reassignment:
            hash_seed=''.join(random.choices(string.ascii_uppercase + string.digits, k = 8))
            self.setup_invite_assignment(hash_seed=hash_seed, invited_committee_name='Emergency_Reviewers')

        self.conference.expire_invitation(self.conference.get_paper_assignment_id(self.match_group.id))

    def deploy_invite(self, assignment_title, enable_reviewer_reassignment, email_template=None):

        ## Add sync process function
        self.conference.invitation_builder.set_paper_group_invitation(self.conference, self.match_group.id)
        self.conference.invitation_builder.set_assignment_invitation(self.conference, self.match_group.id)

        ## Create invite assignment invitation
        hash_seed=''.join(random.choices(string.ascii_uppercase + string.digits, k = 8))
        self.setup_invite_assignment(hash_seed=hash_seed, invited_committee_name=self.match_group.id.split('/')[-1], email_template=email_template, proposed=True)

        ## Create invite assignment edges
        invite_assignments_edges = self.invite_proposed_assignments(assignment_title)

        if self.match_group.id == self.conference.get_reviewers_id() and enable_reviewer_reassignment:
            ## Change the AC console to show the edge browser link
            self.conference.set_reviewer_edit_assignments()

        if self.match_group.id == self.conference.get_area_chairs_id() and enable_reviewer_reassignment:
            ## Change the AC console to show the edge browser link
            self.conference.set_reviewer_edit_assignments(assignment_title=enable_reviewer_reassignment)

        ## Mark the configuration note as deployed in case this is being called through a script
        config_notes = self.client.get_notes(invitation=self.conference.get_invitation_id('Assignment_Configuration', prefix=self.match_group.id), content={ 'title': assignment_title })
        if config_notes:
            note = config_notes[0]
            note.content['status'] = 'Deployed'
            self.client.post_note(note)

        return invite_assignments_edges


