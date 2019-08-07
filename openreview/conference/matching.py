from __future__ import division
import openreview
import csv
from collections import defaultdict

class Matching(object):

    def __init__(self, conference):
        self.conference = conference
        self.client = conference.client

    def _create_edge_invitation(self, id):
        invitation = openreview.Invitation(
            id = id,
            invitees = [self.conference.get_id()],
            readers = [self.conference.get_id()],
            writers = [self.conference.get_id()],
            signatures = [self.conference.get_id()],
            reply = {
                'readers': {
                    'values-regex': self.conference.get_id() + '|~.*'
                },
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
                            'group' : self.conference.get_reviewers_id()
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

        invitation = self._create_edge_invitation(self.conference.get_invitation_id('Reviewing/Conflict'))
        authorids_profiles = {}

        for submission in submissions:
            edges = []
            for profile in user_profiles:
                authorids = submission.content['authorids']
                if submission.details and submission.details.get('original'):
                    authorids = submission.details['original']['content']['authorids']
                if submission.number not in authorids_profiles:
                    profiles = self._get_profiles(authorids)
                    authorids_profiles[submission.number] = profiles
                author_profiles = authorids_profiles[submission.number]
                conflicts = openreview.tools.get_conflicts(author_profiles, profile)
                if conflicts:
                    edges.append(openreview.Edge(
                        invitation = invitation.id,
                        head = submission.id,
                        tail = profile.id,
                        weight = 1,
                        label = ','.join(conflicts),
                        readers = [self.conference.id, profile.id], # do acs need to read all tpms scores?
                        writers = [self.conference.id],
                        signatures = [self.conference.id]
                    ))
            openreview.tools.post_bulk_edges(client = self.client, edges = edges)
        return invitation

    def _build_tpms_scores(self, tpms_score_file, submissions, user_profiles):

        invitation = self._create_edge_invitation(self.conference.get_invitation_id('Reviewing/TPMS_Score'))

        submissions_per_number = { note.number: note for note in submissions }
        profiles_by_email = {}
        for profile in user_profiles:
            for email in profile.content['emails']:
                profiles_by_email[email] = profile

        edges = []
        with open(tpms_score_file) as f:
            for row in csv.reader(f):
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
                        invitation = invitation.id,
                        head = paper_note_id,
                        tail = profile_id,
                        weight = float(score),
                        readers = [self.conference.id, profile_id], # do acs need to read all tpms scores?
                        writers = [self.conference.id],
                        signatures = [self.conference.id]
                    ))

        openreview.tools.post_bulk_edges(client = self.client, edges = edges)
        return invitation

    def _build_affinity_scores(self, affinity_score_file):

        invitation = self._create_edge_invitation(self.conference.get_affinity_score_id())

        edges = []
        with open(affinity_score_file) as f:
            for row in csv.reader(f):
                paper_note_id = row[0]
                profile_id = row[1]
                score = row[2]
                edges.append(openreview.Edge(
                    invitation = invitation.id,
                    head = paper_note_id,
                    tail = profile_id,
                    weight = float(score),
                    readers = [self.conference.id, profile_id], # do acs need to read all tpms scores?
                    writers = [self.conference.id],
                    signatures = [self.conference.id]
                ))

        openreview.tools.post_bulk_edges(client = self.conference.client, edges = edges)
        return invitation

    def _build_subject_area_scores(self, submissions):

        invitation = self._create_edge_invitation(self.conference.get_invitation_id('Reviewing/Subject_Areas_Score'))

        edges = []
        user_subject_areas = list(openreview.tools.iterget_notes(self.client, invitation = self.conference.get_registration_id()))
        for note in submissions:
            note_subject_areas = note.content['subject_areas']
            paper_note_id = note.id
            for subject_area_note in user_subject_areas:
                profile_id = subject_area_note.signatures[0]
                subject_areas = subject_area_note.content['subject_areas']
                score = self._jaccard_similarity(note_subject_areas, subject_areas)
                edges.append(openreview.Edge(
                    invitation = invitation.id,
                    head = paper_note_id,
                    tail = profile_id,
                    weight = float(score),
                    readers = [self.conference.id],
                    writers = [self.conference.id],
                    signatures = [self.conference.id]
                ))

        openreview.tools.post_bulk_edges(client = self.conference.client, edges = edges)
        return invitation

    def _build_config_invitation(self, scores_specification):

        config_inv = openreview.Invitation(
            id = self.conference.get_invitation_id('Reviewing/Assignment_Configuration'),
            invitees = [self.conference.get_id()],
            readers = [self.conference.get_id()],
            writers = [self.conference.get_id()],
            signatures = [self.conference.get_id()],
            reply = {
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
                        'description': 'The number of alternate reviewers to save (per-paper) aggregate score information for',
                        'order': 5
                    },
                    'paper_invitation': {
                        'value': self.conference.get_blind_submission_id(),
                        'required': True,
                        'description': 'Invitation to get the configuration note',
                        'order': 6
                    },
                    'match_group': {
                        'value-radio': [self.conference.get_area_chairs_id(), self.conference.get_reviewers_id()] if self.conference.use_area_chairs else [self.conference.get_reviewers_id()],
                        'required': True,
                        'description': 'Invitation to get the configuration note',
                        'order': 7
                    },
                    'scores_specification': {
                        'value-dict': {},
                        'required': True,
                        'description': 'Manually entered JSON score specification',
                        'order': 8,
                        'default': scores_specification
                    },
                    'aggregate_score_invitation': {
                        'value': self.conference.get_invitation_id('Reviewing/Aggregate_Score'),
                        'required': True,
                        'description': 'Invitation to store aggregated scores',
                        'order': 9
                    },
                    'conflicts_invitation': {
                        'value': self.conference.get_invitation_id('Reviewing/Conflict'),
                        'required': True,
                        'description': 'Invitation to store aggregated scores',
                        'order': 10
                    },
                    'custom_load_invitation': {
                        'value': self.conference.get_invitation_id('Reviewing/Custom_Load'),
                        'required': True,
                        'description': 'Invitation to store aggregated scores',
                        'order': 11
                    },
                    'assignment_invitation': {
                        'value': self.conference.get_invitation_id('Reviewing/Paper_Assignment'),
                        'required': True,
                        'description': 'Invitation to store paper user assignments',
                        'order': 12
                    },
                    'config_invitation': {
                        'value': self.conference.get_invitation_id('Reviewing/Assignment_Configuration')
                    },
                    'status': {
                        'default': 'Initialized',
                        'value-dropdown': ['Initialized', 'Running', 'Error', 'No Solution', 'Complete', 'Deployed']
                    }
                }
            })
        self.client.post_invitation(config_inv)

    def _jaccard_similarity(self, list1, list2):
        set1 = set(list1)
        set2 = set(list2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

    def _search_profiles(self, client, ids, emails):
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

        return profiles, profile_by_email

    def _get_profiles(self, ids_or_emails):
        ids = []
        emails = []
        for member in ids_or_emails:
            if '~' in member:
                ids.append(member)
            else:
                emails.append(member)

        profiles, profile_by_email = self._search_profiles(self.client, ids, emails)

        for email in emails:
            profiles.append(profile_by_email.get(email, openreview.Profile(id = email,
            content = {
                'emails': [email],
                'preferredEmail': email
            })))

        return profiles

    def setup(self, affinity_score_file = None, tpms_score_file = None):

        score_spec = {}

        score_spec[self.conference.get_bid_id()] = {
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

        score_spec[self.conference.get_recommendation_id()] = {
            'weight': 1,
            'default': 0
        }

        reviewers_group = self.conference.client.get_group(self.conference.get_reviewers_id())
        # The reviewers are all emails so convert to tilde ids
        reviewers_group = openreview.tools.replace_members_with_ids(self.client, reviewers_group)
        if not all(['~' in member for member in reviewers_group.members]):
            print('WARNING: not all reviewers have been converted to profile IDs. Members without profiles will not have metadata created.')


        if self.conference.use_area_chairs:
            areachairs_group = self.conference.client.get_group(self.conference.get_area_chairs_id())
            # The areachairs are all emails so convert to tilde ids
            areachairs_group = openreview.tools.replace_members_with_ids(self.client, areachairs_group)
            if not all(['~' in member for member in areachairs_group.members]):
                print('WARNING: not all area chairs have been converted to profile IDs. Members without profiles will not have metadata created.')
            user_profiles = self._get_profiles(reviewers_group.members + areachairs_group.members)
        else:
            user_profiles = self._get_profiles(reviewers_group.members)

        self._create_edge_invitation(self.conference.get_paper_assignment_id())
        self._create_edge_invitation(self.conference.get_invitation_id('Reviewing/Aggregate_Score'))
        self._create_edge_invitation(self.conference.get_invitation_id('Reviewing/Custom_Load'))
        self._create_edge_invitation(self.conference.get_invitation_id('Reviewing/Conflict'))

        submissions = list(openreview.tools.iterget_notes(
            self.conference.client, invitation = self.conference.get_blind_submission_id(), details='original'))

        if tpms_score_file:
            invitation = self._build_tpms_scores(tpms_score_file, submissions, user_profiles)
            score_spec[invitation.id] = {
                'weight': 1,
                'default': 0
            }

        if affinity_score_file:
            invitation = self._build_affinity_scores(affinity_score_file)
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

        # Get the configuration note to check the group to assign
        client = self.conference.client
        notes = client.get_notes(invitation = self.conference.get_id() + '/-/Reviewing/Assignment_Configuration', content = { 'title': assingment_title })
        if self.conference.use_area_chairs:
            self.conference.set_area_chairs(enable_reviewer_reassignment = True)

        if notes:
            configuration_note = notes[0]
            match_group = configuration_note.content['match_group']
            is_area_chair = self.conference.get_area_chairs_id() == match_group
            submissions = openreview.tools.iterget_notes(client, invitation = self.conference.get_blind_submission_id())
            assignment_edges = openreview.tools.iterget_edges(client, invitation = self.conference.get_paper_assignment_id(), label = assingment_title)

            paper_by_forum = { n.forum: n for n in submissions }

            for edge in assignment_edges:
                paper_number = paper_by_forum.get(edge.head).number
                user = edge.tail
                new_assigned_group = self.conference.set_assignment(user, paper_number, is_area_chair)
                print(new_assigned_group)

        else:
            raise openreview.OpenReviewException('Configuration not found for ' + assingment_title)




