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
import tld
import re
from tqdm import tqdm
from .. import tools

def _jaccard_similarity(list1, list2):
    '''
    Return a score, indicating the similarity between two lists
    '''
    set1 = set(list1)
    set2 = set(list2)
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)

def _get_profiles(client, ids_or_emails):
    '''
    Helper function that repeatedly queries for profiles, given IDs and emails.
    Useful for getting more Profiles than the server will return by default (1000)
    '''
    ids = []
    emails = []
    for member in ids_or_emails:
        if '~' in member:
            ids.append(member)
        else:
            emails.append(member)

    profiles = []
    profile_by_email = {}

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_profiles = client.search_profiles(ids=batch_ids)
        profiles.extend(batch_profiles)

    for j in range(0, len(emails), batch_size):
        batch_emails = emails[j:j+batch_size]
        batch_profile_by_email = client.search_profiles(confirmedEmails=batch_emails)
        profile_by_email.update(batch_profile_by_email)

    for email in emails:
        profiles.append(profile_by_email.get(email, openreview.Profile(
            id=email,
            content={
                'emails': [email],
                'preferredEmail': email
            })))

    return profiles

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
    def __init__(self, conference, match_group):
        self.conference = conference
        self.client = conference.client
        self.match_group = match_group
        self.is_reviewer = conference.get_reviewers_id() == match_group.id
        self.is_area_chair = conference.get_area_chairs_id() == match_group.id
        self.is_senior_area_chair = conference.get_senior_area_chairs_id() == match_group.id
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
        edge_writers = [self.conference.get_id()]
        edge_signatures = [self.conference.get_id() + '$', self.conference.get_program_chairs_id()]
        edge_nonreaders = {
            'values-regex': self.conference.get_authors_id(number='.*')
        }
        if self.is_reviewer:
            if self.conference.use_senior_area_chairs:
                edge_readers.append(self.conference.get_senior_area_chairs_id(number=paper_number))
            if self.conference.use_area_chairs:
                edge_readers.append(self.conference.get_area_chairs_id(number=paper_number))

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

            if is_assignment_invitation:
                if self.conference.use_senior_area_chairs:
                    edge_invitees.append(self.conference.get_senior_area_chairs_id())
                    edge_writers.append(self.conference.get_senior_area_chairs_id(number=paper_number))
                    edge_signatures.append(self.conference.get_senior_area_chairs_id(number=paper_number))

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
                'value-dropdown': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                'required': True
            }
            edge_label=None
        if self.is_senior_area_chair:
            edge_head_type = 'Profile'
            edge_head_query = {
                'group' : self.conference.get_area_chairs_id()
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
            readers=[self.conference.get_id(), self.conference.get_senior_area_chairs_id(), self.conference.get_area_chairs_id()],
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

    def _build_conflicts(self, submissions, user_profiles):
        if self.is_senior_area_chair:
            ac_group = self.client.get_group(self.conference.get_area_chairs_id())
            ac_profiles = _get_profiles(self.client, ac_group.members)
            return self._build_profile_conflicts(ac_profiles, user_profiles)
        return self._build_note_conflicts(submissions, user_profiles)

    def _build_note_conflicts(self, submissions, user_profiles):
        '''
        Create conflict edges between the given Notes and Profiles
        '''
        invitation = self._create_edge_invitation(self.conference.get_conflict_score_id(self.match_group.id))
        # Get profile info from the match group
        user_profiles_info = [openreview.tools.get_profile_info(p) for p in user_profiles]

        edges = []

        for submission in tqdm(submissions, total=len(submissions), desc='_build_conflicts'):
            # Get author profiles
            authorids = submission.content['authorids']
            if submission.details and submission.details.get('original'):
                authorids = submission.details['original']['content']['authorids']

            # Extract domains from each profile
            author_profiles = _get_profiles(self.client, authorids)
            author_domains = set()
            author_emails = set()
            author_relations = set()

            for author_profile in author_profiles:
                author_info = openreview.tools.get_profile_info(author_profile)
                author_domains.update(author_info['domains'])
                author_emails.update(author_info['emails'])
                author_relations.update(author_info['relations'])

            # Compute conflicts for each user and all the paper authors
            for user_info in user_profiles_info:
                conflicts = set()
                conflicts.update(author_domains.intersection(user_info['domains']))
                conflicts.update(author_relations.intersection(user_info['emails']))
                conflicts.update(author_emails.intersection(user_info['relations']))
                conflicts.update(author_emails.intersection(user_info['emails']))
                if conflicts:
                    edges.append(openreview.Edge(
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
        user_profiles_info = [openreview.tools.get_profile_info(p) for p in user_profiles]
        head_profiles_info = [openreview.tools.get_profile_info(p) for p in head_profiles]

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
                    edges.append(openreview.Edge(
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

                    edges.append(openreview.Edge(
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

    def _build_scores(self, score_invitation_id, score_file, submissions):
        if self.is_senior_area_chair:
            return self._build_profile_scores(score_invitation_id, score_file)
        return self._build_note_scores(score_invitation_id, score_file, submissions)

    def _build_note_scores(self, score_invitation_id, score_file, submissions):
        '''
        Given a csv file with affinity scores, create score edges
        '''
        invitation = self._create_edge_invitation(score_invitation_id)

        submissions_per_id = {note.id: note.number for note in submissions}

        edges = []
        deleted_papers = set()
        with open(score_file) as file_handle:
            for row in tqdm(csv.reader(file_handle), desc='_build_scores'):
                paper_note_id = row[0]
                paper_number = submissions_per_id.get(paper_note_id)
                if paper_number:
                    profile_id = row[1]
                    score = row[2]
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

    def _build_profile_scores(self, score_invitation_id, score_file):
        '''
        Given a csv file with affinity scores, create score edges
        '''
        invitation = self._create_edge_invitation(score_invitation_id)
        edges = []
        with open(score_file) as file_handle:
            for row in tqdm(csv.reader(file_handle), desc='_build_scores'):
                edges.append(openreview.Edge(
                    invitation=invitation.id,
                    head=row[0],
                    tail=row[1],
                    weight=float(row[2]),
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
        user_subject_areas = list(openreview.tools.iterget_notes(
            self.client,
            invitation=self.conference.get_registration_id(self.match_group.id)))

        for note in tqdm(submissions, total=len(submissions), desc='_build_subject_area_scores'):
            note_subject_areas = note.content['subject_areas']
            paper_note_id = note.id
            for subject_area_note in user_subject_areas:
                profile_id = subject_area_note.signatures[0]
                if profile_id in self.match_group.members:
                    subject_areas = subject_area_note.content['subject_areas']
                    score = _jaccard_similarity(note_subject_areas, subject_areas)
                    edges.append(openreview.Edge(
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

        openreview.tools.post_bulk_edges(client=self.conference.client, edges=edges)
        # Perform sanity check
        edges_posted = self.conference.client.get_edges_count(invitation=invitation.id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of edges! Scores found: {0}, Edges posted: {1}'.format(len(edges), edges_posted))
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
                        'value-regex': '.{1,250}',
                        'required': True,
                        'description': 'Title of the configuration.',
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
                        'value-regex': self.conference.get_area_chairs_id() if self.is_senior_area_chair else self.conference.get_blind_submission_id() + '.*',
                        'default': self.conference.get_area_chairs_id() if self.is_senior_area_chair else self.conference.get_blind_submission_id(),
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
                        'value-radio': ['MinMax', 'FairFlow'],
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
                            'Deployment Error'
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
                        'description': 'Select "Yes" only if you want to allow assignments with 0 scores',
                        'value-radio': ['Yes', 'No'],
                        'required': False,
                        'default': 'No',
                        'order': 20
                    }
                }
            })
        self.client.post_invitation(config_inv)

    def setup(self, affinity_score_file=None, tpms_score_file=None, elmo_score_file=None, build_conflicts=False):
        '''
        Build all the invitations and edges necessary to run a match
        '''
        score_spec = {}

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
        if not all(['~' in member for member in self.match_group.members]):
            print(
                'WARNING: not all reviewers have been converted to profile IDs.',
                'Members without profiles will not have metadata created.')

        user_profiles = _get_profiles(self.client, self.match_group.members)

        invitation=self._create_edge_invitation(self.conference.get_paper_assignment_id(self.match_group.id))
        if not self.is_senior_area_chair:
            with open(os.path.join(os.path.dirname(__file__), 'templates/proposed_assignment_pre_process.py')) as f:
                content = f.read()
                content = content.replace("CUSTOM_MAX_PAPERS_INVITATION_ID = ''", "CUSTOM_MAX_PAPERS_INVITATION_ID = '" + self.conference.get_custom_max_papers_id(self.match_group.id) + "'")
                invitation.preprocess=content
                self.client.post_invitation(invitation)

        self._create_edge_invitation(self.conference.get_paper_assignment_id(self.match_group.id, deployed=True))
        self._create_edge_invitation(self._get_edge_invitation_id('Aggregate_Score'))
        self._create_edge_invitation(self.conference.get_custom_max_papers_id(self.match_group.id))
        self._create_edge_invitation(self._get_edge_invitation_id('Custom_User_Demands'))

        submissions = list(openreview.tools.iterget_notes(
            self.conference.client,
            invitation=self.conference.get_blind_submission_id(),
            details='original'))

        if tpms_score_file:
            invitation = self._build_tpms_scores(tpms_score_file, submissions, user_profiles)
            score_spec[invitation.id] = {
                'weight': 1,
                'default': 0
            }

        if affinity_score_file:
            invitation = self._build_scores(
                self.conference.get_affinity_score_id(self.match_group.id),
                affinity_score_file,
                submissions
            )
            score_spec[invitation.id] = {
                'weight': 1,
                'default': 0
            }

        if elmo_score_file:
            invitation = self._build_scores(
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

        if build_conflicts:
            self._build_conflicts(submissions, user_profiles)

        self._build_config_invitation(score_spec)

    def setup_invite_assignment(self, hash_seed, assignment_title=None, due_date=None):

        recruitment_invitation_id=self.conference.get_invitation_id('Proposed_Assignment_Recruitment' if assignment_title else 'Assignment_Recruitment', prefix=self.match_group.id)

        invitation=self._create_edge_invitation(self.conference.get_paper_assignment_id(self.match_group.id, invite=True), any_tail=True, default_label='Invite')
        with open(os.path.join(os.path.dirname(__file__), 'templates/invite_assignment_pre_process.py')) as pre:
            with open(os.path.join(os.path.dirname(__file__), 'templates/invite_assignment_post_process.py')) as post:
                pre_content = pre.read()
                post_content = post.read()
                post_content = post_content.replace("SHORT_PHRASE = ''", "SHORT_PHRASE = '" + self.conference.short_name + "'")
                post_content = post_content.replace("RECRUITMENT_INVITATION_ID = ''", "RECRUITMENT_INVITATION_ID = '" + recruitment_invitation_id + "'")
                if assignment_title:
                    pre_content = pre_content.replace("ASSIGNMENT_INVITATION_ID = ''", "ASSIGNMENT_INVITATION_ID = '" + self.conference.get_paper_assignment_id(self.match_group.id) + "'")
                    pre_content = pre_content.replace("ASSIGNMENT_LABEL = None", "ASSIGNMENT_LABEL = '" + assignment_title + "'")
                    post_content = post_content.replace("ASSIGNMENT_INVITATION_ID = ''", "ASSIGNMENT_INVITATION_ID = '" + self.conference.get_paper_assignment_id(self.match_group.id) + "'")
                    post_content = post_content.replace("ASSIGNMENT_LABEL = None", "ASSIGNMENT_LABEL = '" + assignment_title + "'")
                    post_content = post_content.replace("REVIEWERS_INVITED_ID = ''", "REVIEWERS_INVITED_ID = '" + self.conference.get_committee_id(name='External_Reviewers/Invited') + "'")
                else:
                    pre_content = pre_content.replace("ASSIGNMENT_INVITATION_ID = ''", "ASSIGNMENT_INVITATION_ID = '" + self.conference.get_paper_assignment_id(self.match_group.id, deployed=True) + "'")
                    post_content = post_content.replace("ASSIGNMENT_INVITATION_ID = ''", "ASSIGNMENT_INVITATION_ID = '" + self.conference.get_paper_assignment_id(self.match_group.id, deployed=True) + "'")

                post_content = post_content.replace("HASH_SEED = ''", "HASH_SEED = '" + hash_seed + "'")

                invitation.preprocess=pre_content
                invitation.process=post_content
                invitation.multiReply=False
                invitation.signatures=[self.conference.get_program_chairs_id()] ## Program Chairs have permission to see full profile data
                invite_assignment_invitation=self.client.post_invitation(invitation)

        invitation = self.conference.invitation_builder.set_paper_recruitment_invitation(self.conference, recruitment_invitation_id, self.match_group.id, hash_seed, assignment_title, due_date)
        invitation = self.conference.webfield_builder.set_paper_recruitment_page(self.conference, invitation)

        ## Only for reviewers, allow ACs and SACs to review the proposed assignments
        if assignment_title and self.match_group.id == self.conference.get_reviewers_id():
            self.conference.set_external_reviewer_recruitment_groups()
            invitation=self.client.get_invitation(self.conference.get_paper_assignment_id(self.match_group.id))
            invitation.duedate=tools.datetime_millis(due_date)
            invitation.expdate=tools.datetime_millis(due_date + datetime.timedelta(minutes= 30)) if due_date else None
            invitation=self.client.post_invitation(invitation)
            invitation = self.conference.webfield_builder.set_reviewer_proposed_assignment_page(self.conference, invitation, assignment_title, invite_assignment_invitation)


        return invite_assignment_invitation


    def deploy_acs(self, assignment_title, overwrite):

        papers = list(openreview.tools.iterget_notes(self.client, invitation=self.conference.get_blind_submission_id()))
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

        papers = list(openreview.tools.iterget_notes(self.client, invitation=self.conference.get_blind_submission_id()))
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
        review_name = 'Meta_Review' if self.is_area_chair else 'Official_Review'
        reviewer_name = self.conference.area_chairs_name if self.is_area_chair else self.conference.reviewers_name

        papers = list(openreview.tools.iterget_notes(self.client, invitation=self.conference.get_blind_submission_id()))
        reviews = self.client.get_notes(invitation=self.conference.get_invitation_id(review_name, number='.*'), limit=1)
        print('REviews', reviews, self.conference.get_invitation_id(review_name, number='.*'))
        proposed_assignment_edges =  { g['id']['head']: g['values'] for g in self.client.get_grouped_edges(invitation=self.conference.get_paper_assignment_id(self.match_group.id),
            label=assignment_title, groupby='head', select=None)}
        print('proposed_assignment_edges', proposed_assignment_edges)
        assignment_edges = []
        assignment_invitation_id = self.conference.get_paper_assignment_id(self.match_group.id, deployed=True)
        current_assignment_edges =  { g['id']['head']: g['values'] for g in self.client.get_grouped_edges(invitation=assignment_invitation_id, groupby='head', select=None)}

        if overwrite:
            if reviews:
                raise openreview.OpenReviewException('Can not overwrite assignments when there are reviews posted.')
            ## Delete current assignment edges with a ddate in case we need to do rollback
            self.client.delete_edges(invitation=assignment_invitation_id, wait_to_finish=True, soft_delete=True)

        for paper in tqdm(papers, total=len(papers)):

            paper_group = self.client.get_group(self.conference.get_committee_id(name=reviewer_name, number=paper.number))

            if overwrite:
                paper_group.members = []
            if paper.id in proposed_assignment_edges:
                proposed_edges=proposed_assignment_edges[paper.id]
                for proposed_edge in proposed_edges:
                    print('proposed_edge', proposed_edge)
                    paper_group.members.append(proposed_edge['tail'])
                    assignment_edges.append(openreview.Edge(
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

            self.client.post_group(paper_group)

        print('POsting assignments edges', len(assignment_edges))
        openreview.tools.post_bulk_edges(client=self.client, edges=assignment_edges)

    def deploy_sac_assignments(self, assignment_title, overwrite):

        print('deploy_sac_assignments', assignment_title)

        papers = list(openreview.tools.iterget_notes(self.client, invitation=self.conference.get_blind_submission_id()))

        assignment_edges =  { g['id']['head']: g['values'] for g in self.client.get_grouped_edges(invitation=self.conference.get_paper_assignment_id(self.match_group.id),
            label=assignment_title, groupby='head', select='tail')}

        ac_groups = {g.id:g for g in openreview.tools.iterget_groups(self.client, regex=self.conference.get_area_chairs_id('.*'))}

        if not papers:
            raise openreview.OpenReviewException('No submissions to deploy SAC assignment')

        for paper in papers:

            ac_group_id=self.conference.get_area_chairs_id(paper.number)

            ac_group=ac_groups.get(ac_group_id)

            if ac_group:
                if len(ac_group.members) == 0:
                    raise openreview.OpenReviewException('AC assignments must be deployed first')

                for ac in ac_group.members:
                    sac_assignments = assignment_edges.get(ac, [])

                    for sac_assignment in sac_assignments:
                        sac=sac_assignment['tail']
                        print('sac assignment', sac, ac_group.id)
                        sac_group_id=ac_group.id.replace(self.conference.area_chairs_name, self.conference.senior_area_chairs_name)
                        print(sac_group_id)
                        sac_group=self.client.get_group(sac_group_id)
                        if overwrite:
                            sac_group.members=[]
                        sac_group.members.append(sac)
                        self.client.post_group(sac_group)


    def deploy(self, assignment_title, overwrite=False, enable_reviewer_reassignment=False):
        '''
        WARNING: This function untested

        '''

        if self.conference.legacy_anonids:
            if self.is_area_chair:
                return self.deploy_acs(assignment_title, overwrite)

            return self.deploy_reviewers(assignment_title, overwrite)


        if self.match_group.id == self.conference.get_senior_area_chairs_id():
            return self.deploy_sac_assignments(assignment_title, overwrite)

        ## Deploy assingments creating groups and assignment edges
        self.deploy_assignments(assignment_title, overwrite)

        ## Add sync process function
        self.conference.invitation_builder.set_paper_group_invitation(self.conference, self.match_group.id)
        self.conference.invitation_builder.set_assignment_invitation(self.conference, self.match_group.id)

        if self.match_group.id == self.conference.get_reviewers_id() and enable_reviewer_reassignment:
            hash_seed=''.join(random.choices(string.ascii_uppercase + string.digits, k = 8))
            self.setup_invite_assignment(hash_seed=hash_seed)

