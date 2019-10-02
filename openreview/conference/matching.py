'''
A module containing tools for matching and and main Matching instance class
'''

from __future__ import division
import csv

import openreview
import tld

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

    def _get_edge_invitation_id(self, edge_name):
        '''
        Returns a correctly formatted edge invitation ID for this Matching's match group
        '''
        return self.conference.get_invitation_id(edge_name, prefix=self.match_group.id)

    def _create_edge_invitation(self, edge_id, extendable_readers=False):
        '''
        Creates an edge invitation given an edge name
        e.g. "Affinity_Score"
        '''

        readers = {
            'values': [self.conference.get_id()]
        }

        if extendable_readers:
            regex = self.conference.get_id() + '|~.*|.*@.*'
            if self.match_group.id == self.conference.get_reviewers_id() and self.conference.use_area_chairs:
                regex += '|' + self.conference.get_area_chairs_id()

            readers = {
                'values-regex': regex
            }

        invitation = openreview.Invitation(
            id=edge_id,
            invitees=[self.conference.get_id()],
            readers=[self.conference.get_id()],
            writers=[self.conference.get_id()],
            signatures=[self.conference.get_id()],
            reply={
                'readers': readers,
                'writers': {
                    'values': [self.conference.get_id()]
                },
                'signatures': {
                    'values': [self.conference.get_id()]
                },
                'content': {
                    'head': {
                        'type': 'Note',
                        'query' : {
                            'invitation' : self.conference.get_blind_submission_id()
                        }
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
        invitation = self._create_edge_invitation(self.conference.get_conflict_score_id(self.match_group.id), extendable_readers=True)
        authorids_profiles = {}

        for submission in submissions:
            edges = []
            for profile in user_profiles:
                authorids = submission.content['authorids']
                if submission.details and submission.details.get('original'):
                    authorids = submission.details['original']['content']['authorids']
                if submission.number not in authorids_profiles:
                    profiles = _get_profiles(self.client, authorids)
                    authorids_profiles[submission.number] = profiles
                author_profiles = authorids_profiles[submission.number]
                conflicts = openreview.tools.get_conflicts(author_profiles, profile)
                if conflicts:
                    edges.append(openreview.Edge(
                        invitation=invitation.id,
                        head=submission.id,
                        tail=profile.id,
                        weight=-1,
                        label=_conflict_label(conflicts),
                        readers=[self.conference.id, profile.id],
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))
            openreview.tools.post_bulk_edges(client=self.client, edges=edges)
        return invitation

    def _build_tpms_scores(self, tpms_score_file, submissions, user_profiles):
        '''
        Create tpms score edges given a csv file with scores, papers, and profiles.
        '''
        # pylint: disable=too-many-locals
        invitation = self._create_edge_invitation(self._get_edge_invitation_id('TPMS_Score'), extendable_readers=True)

        submissions_per_number = {note.number: note for note in submissions}
        profiles_by_email = {}
        for profile in user_profiles:
            for email in profile.content['emails']:
                profiles_by_email[email] = profile

        edges = []
        with open(tpms_score_file) as file_handle:
            for row in csv.reader(file_handle):
                number = int(row[0])
                if number in submissions_per_number:
                    paper_note_id = submissions_per_number[number].id
                    profile = profiles_by_email.get(row[1])
                    if profile:
                        profile_id = profile.id
                    else:
                        profile_id = row[1]

                    score = row[2]
                    edges.append(openreview.Edge(
                        invitation=invitation.id,
                        head=paper_note_id,
                        tail=profile_id,
                        weight=float(score),
                        readers=[self.conference.id, profile.id],
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)
        return invitation

    def _build_scores(self, score_invitation_id, score_file):
        '''
        Given a csv file with affinity scores, create score edges
        '''
        invitation = self._create_edge_invitation(score_invitation_id, extendable_readers=True)

        edges = []
        with open(score_file) as file_handle:
            for row in csv.reader(file_handle):
                paper_note_id = row[0]
                profile_id = row[1]
                score = row[2]
                edges.append(openreview.Edge(
                    invitation=invitation.id,
                    head=paper_note_id,
                    tail=profile_id,
                    weight=float(score),
                    readers=[self.conference.id, profile_id],
                    writers=[self.conference.id],
                    signatures=[self.conference.id]
                ))

        openreview.tools.post_bulk_edges(client=self.conference.client, edges=edges)
        return invitation

    def _build_subject_area_scores(self, submissions):
        '''
        Create subject area scores between all users in the match group and all given submissions
        '''
        invitation = self._create_edge_invitation(self._get_edge_invitation_id('Subject_Areas_Score'), extendable_readers=True)

        edges = []
        user_subject_areas = list(openreview.tools.iterget_notes(
            self.client,
            invitation=self.conference.get_registration_id()))

        for note in submissions:
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
                        readers=[self.conference.id],
                        writers=[self.conference.id],
                        signatures=[self.conference.id]
                    ))

        openreview.tools.post_bulk_edges(client=self.conference.client, edges=edges)
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
                    'max_users': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Max number of reviewers that can review a paper',
                        'order': 2
                    },
                    'min_users': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Min number of reviewers required to review a paper',
                        'order': 3
                    },
                    'max_papers': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Max number of reviews a person has to do',
                        'order': 4
                    },
                    'min_papers': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'Min number of reviews a person should do',
                        'order': 5
                    },
                    'alternates': {
                        'value-regex': '[0-9]+',
                        'required': True,
                        'description': 'The number of alternate reviewers to save (per-paper)',
                        'order': 5
                    },
                    'paper_invitation': {
                        'value': self.conference.get_blind_submission_id(),
                        'required': True,
                        'description': 'Invitation to get the configuration note',
                        'order': 6
                    },
                    'match_group': {
                        'value': self.match_group.id,
                        'required': True,
                        'description': 'Invitation to get the configuration note',
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
                        'value': self._get_edge_invitation_id('Aggregate_Score'),
                        'required': True,
                        'description': 'Invitation to store aggregated scores',
                        'order': 9
                    },
                    'conflicts_invitation': {
                        'value': self.conference.get_conflict_score_id(self.match_group.id),
                        'required': True,
                        'description': 'Invitation to store aggregated scores',
                        'order': 10
                    },
                    'custom_load_invitation': {
                        'value': self._get_edge_invitation_id('Custom_Load'),
                        'required': True,
                        'description': 'Invitation to store aggregated scores',
                        'order': 11
                    },
                    'assignment_invitation': {
                        'value': self.conference.get_paper_assignment_id(self.match_group.id),
                        'required': True,
                        'description': 'Invitation to store paper user assignments',
                        'order': 12
                    },
                    'config_invitation': {
                        'value': self._get_edge_invitation_id('Assignment_Configuration')
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
                        ]
                    },
                    'error_message': {
                        'value-regex': '.*',
                        'required': False
                    }
                }
            })
        self.client.post_invitation(config_inv)

    def setup(self, affinity_score_file=None, tpms_score_file=None, elmo_score_file=None):
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
        self._create_edge_invitation(self._get_edge_invitation_id('Custom_Load'), extendable_readers=True)

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
                affinity_score_file
            )
            score_spec[invitation.id] = {
                'weight': 1,
                'default': 0
            }

        if elmo_score_file:
            invitation = self._build_scores(
                self.conference.get_elmo_score_id(self.match_group.id),
                elmo_score_file
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

        self._build_conflicts(submissions, user_profiles)
        self._build_config_invitation(score_spec)


    def deploy(self, assingment_title):
        '''
        WARNING: This function untested

        '''
        # pylint: disable=too-many-locals

        # Get the configuration note to check the group to assign
        client = self.conference.client
        notes = client.get_notes(
            invitation=self.match_group.id + '/-/Assignment_Configuration',
            content={'title': assingment_title})

        if notes:
            configuration_note = notes[0]
            match_group = configuration_note.content['match_group']
            is_area_chair = self.conference.get_area_chairs_id() == match_group

            submissions = openreview.tools.iterget_notes(
                client,
                invitation=self.conference.get_blind_submission_id())

            assignment_edges = openreview.tools.iterget_edges(
                client,
                invitation=self.conference.get_paper_assignment_id(self.match_group.id),
                label=assingment_title)

            paper_by_forum = {n.forum: n for n in submissions}

            for edge in assignment_edges:
                paper_number = paper_by_forum.get(edge.head).number
                user = edge.tail
                new_assigned_group = self.conference.set_assignment(user, paper_number, is_area_chair)
                print(new_assigned_group)

        else:
            raise openreview.OpenReviewException('Configuration not found for ' + assingment_title)
