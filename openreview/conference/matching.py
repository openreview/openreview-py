'''
A module containing tools for matching and and main Matching instance class
'''

from __future__ import division
import csv
import openreview
import tld
import re
from tqdm import tqdm

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
        batch_profile_by_email = client.search_profiles(emails=batch_emails)
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
        self.is_area_chair = conference.get_area_chairs_id() == match_group.id
        self.should_read_by_area_chair = not self.is_area_chair and conference.has_area_chairs

    def _get_edge_invitation_id(self, edge_name):
        '''
        Returns a correctly formatted edge invitation ID for this Matching's match group
        '''
        return self.conference.get_invitation_id(edge_name, prefix=self.match_group.id)

    def _get_edge_readers(self, tail):
        readers = [self.conference.id]
        if self.should_read_by_area_chair:
            readers.append(self.conference.get_area_chairs_id())
        readers.append(tail)
        return readers

    def _create_edge_invitation(self, edge_id):
        '''
        Creates an edge invitation given an edge name
        e.g. "Affinity_Score"
        '''

        edge_readers = [self.conference.get_id()]
        if self.should_read_by_area_chair:
            ## Area Chairs should read the edges of the reviewer invitations.
            edge_readers.append(self.conference.get_area_chairs_id())

        readers = {
            'values-copied': edge_readers + ['{tail}']
        }

        edge_head_type = 'Note'
        edge_head_query = {
            'invitation' : self.conference.get_blind_submission_id()
        }
        if 'Custom_Max_Papers' in edge_id:
            edge_head_type = 'Group'
            edge_head_query = {
                'id' : edge_id.split('/-/')[0]
            }

        invitation = openreview.Invitation(
            id=edge_id,
            invitees=[self.conference.get_id()],
            readers=[self.conference.get_id(), self.conference.get_area_chairs_id()],
            writers=[self.conference.get_id()],
            signatures=[self.conference.get_id()],
            reply={
                'readers': readers,
                'nonreaders': {
                    'values-regex': self.conference.get_authors_id(number='.*')
                },
                'writers': {
                    'values': [self.conference.get_id()]
                },
                'signatures': {
                    'values': [self.conference.get_id()]
                },
                'content': {
                    'head': {
                        'type': edge_head_type,
                        'query' : edge_head_query
                    },
                    'tail': {
                        'type': 'Profile',
                        'query' : {
                            'group' : self.match_group.id
                        }
                    },
                    'weight': {
                        'value-regex': r'[-+]?[0-9]*\.?[0-9]*'
                    },
                    'label': {
                        'value-regex': '.*'
                    }
                }
            })

        invitation = self.client.post_invitation(invitation)
        self.client.delete_edges(invitation.id)
        return invitation

    def _build_conflicts(self, submissions, user_profiles):
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
                        label=_conflict_label(conflicts),
                        readers=self._get_edge_readers(tail=user_info['id']),
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))

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

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)
        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation.id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of TPMS edges! Input file:{0}, Scores found: {1}, Edges posted: {2}'.format(tpms_score_file, len(edges), edges_posted))
        return invitation

    def _build_scores(self, score_invitation_id, score_file, submissions):
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
            invitees=[self.conference.get_id()],
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
                        'value-regex': self.conference.get_blind_submission_id() + '.*',
                        'default': self.conference.get_blind_submission_id(),
                        'required': True,
                        'description': 'Invitation to get the configuration note',
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
                        'order': 9
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
                        'order': 11
                    },
                    'custom_user_demand_invitation': {
                        'value-regex': '{}/.*/-/Custom_User_Demands$'.format(self.conference.id),
                        'default': '{}/-/Custom_User_Demands'.format(self.match_group.id),
                        'description': 'Invitation to store custom number of users required by papers',
                        'order': 12,
                        'required': False
                    },
                    'custom_max_papers_invitation': {
                        'value-regex': '{}/.*/-/Custom_Max_Papers$'.format(self.conference.id),
                        'default': '{}/-/Custom_Max_Papers'.format(self.match_group.id),
                        'description': "Invitation to store custom max number of papers that can be assigned to reviewers",
                        'order': 13,
                        'required': False
                    },
                    'config_invitation': {
                        'value': self._get_edge_invitation_id('Assignment_Configuration'),
                        'order': 14
                    },
                    'solver': {
                        'value-radio': ['MinMax', 'FairFlow'],
                        'default': 'MinMax',
                        'required': True,
                        'order': 15
                    },
                    'status': {
                        'default': 'Initialized',
                        'value-dropdown': [
                            'Initialized',
                            'Running',
                            'Error',
                            'No Solution',
                            'Complete',
                            'Deployed'
                        ],
                        'order': 16
                    },
                    'error_message': {
                        'value-regex': '.*',
                        'required': False,
                        'order': 17
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

        self._create_edge_invitation(self.conference.get_paper_assignment_id(self.match_group.id))
        self._create_edge_invitation(self._get_edge_invitation_id('Aggregate_Score'))
        self._create_edge_invitation(self._get_edge_invitation_id('Custom_Max_Papers'))
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


    def deploy(self, assignment_title, is_area_chair, overwrite):
        '''
        WARNING: This function untested

        '''
        # pylint: disable=too-many-locals

        # Get the configuration note to check the group to assign
        client = self.conference.client

        submissions = openreview.tools.iterget_notes(
            client,
            invitation=self.conference.get_blind_submission_id())

        if overwrite:
            groups = []
            if is_area_chair:
                groups.extend(client.get_groups(regex=self.conference.get_id()+'/Paper[0-9]+/Area_Chairs'))
                groups.extend(client.get_groups(regex=self.conference.get_id()+'/Paper[0-9]+/Area_Chair[0-9]+'))
            else:
                groups.extend(client.get_groups(regex=self.conference.get_id()+'/Paper[0-9]+/Reviewers'))
                groups.extend(client.get_groups(regex=self.conference.get_id()+'/Paper[0-9]+/AnonReviewer[0-9]+'))
            for group in tqdm(groups, total=len(groups), desc='Deleting groups'):
                client.delete_group(group.id)

        edges_count = client.get_edges_count(invitation=self.conference.get_paper_assignment_id(self.match_group.id), label=assignment_title)

        assignment_edges = openreview.tools.iterget_edges(
            client,
            invitation=self.conference.get_paper_assignment_id(self.match_group.id),
            label=assignment_title)

        paper_by_forum = {n.forum: n for n in submissions}

        for edge in tqdm(assignment_edges, total=edges_count):
            if edge.head in paper_by_forum:
                paper_number = paper_by_forum.get(edge.head).number
                user = edge.tail
                self.conference.set_assignment(user, paper_number, self.is_area_chair)
            else:
                print('paper not found', edge.head)
