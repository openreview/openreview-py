import csv
import datetime
import os
import openreview
from openreview.api import Edge
from openreview.api import Invitation
from tqdm import tqdm
import time
import random
import string
from .. import tools
from operator import concat
from functools import reduce

class Matching(object):

    def __init__(self, venue, match_group, alternate_matching_group=None):
        self.venue = venue
        self.client = venue.client
        self.match_group = match_group
        self.alternate_matching_group = alternate_matching_group
        self.is_reviewer = venue.get_reviewers_id() == match_group.id
        self.is_area_chair = venue.get_area_chairs_id() == match_group.id
        self.is_senior_area_chair = venue.get_senior_area_chairs_id() == match_group.id
        self.is_ethics_reviewer = venue.get_ethics_reviewers_id() == match_group.id
        self.should_read_by_area_chair = venue.get_reviewers_id() == match_group.id and venue.use_area_chairs
        self.sac_profile_info = None #expects a policy, for example: openreview.tools.get_sac_profile_info
        self.sac_n_years = None

    def _get_edge_invitation_id(self, edge_name):
        return self.venue.get_invitation_id(edge_name, prefix=self.match_group.id)

    def _get_edge_readers(self, tail):
        readers = [self.venue.venue_id]
        if self.should_read_by_area_chair:
            if self.venue.use_senior_area_chairs:
                readers.append(self.venue.get_senior_area_chairs_id())
            readers.append(self.venue.get_area_chairs_id())
        readers.append(tail)
        return readers

    def get_committee_name(self):
        if self.is_reviewer:
            return 'Reviewers'
        if self.is_area_chair:
            return 'Area_Chairs'
        if self.is_senior_area_chair:
            return 'Senior_Area_Chairs'
        if self.is_ethics_reviewer:
            return 'Ethics_Reviewers'
        return self.match_group.id.split('/')[-1]

    def _create_edge_invitation(self, edge_id, any_tail=False, default_label=None):

        venue = self.venue
        venue_id = venue.venue_id
        
        is_assignment_invitation=edge_id.endswith('Assignment') or edge_id.endswith('Aggregate_Score')
        paper_number = '${{2/head}/number}' if is_assignment_invitation else None

        assignment_or_proposed = edge_id.endswith('Assignment')

        edge_invitees = [venue_id, venue.support_user]
        edge_readers = [venue_id]
        invitation_readers = [venue_id]
        edge_writers = [venue_id]
        edge_signatures = [venue_id + '$', venue.get_program_chairs_id()]
        edge_nonreaders = []

        if edge_id.endswith('Affinity_Score'):
            edge_nonreaders = [venue.get_authors_id(number='${{2/head}/number}')]

        if self.is_reviewer:
            if venue.use_senior_area_chairs:
                edge_readers.append(venue.get_senior_area_chairs_id(number=paper_number))
                invitation_readers.append(venue.get_senior_area_chairs_id())
            if venue.use_area_chairs:
                edge_readers.append(venue.get_area_chairs_id(number=paper_number))
                invitation_readers.append(venue.get_area_chairs_id())

            if is_assignment_invitation:
                if venue.use_senior_area_chairs:
                    edge_invitees.append(venue.get_senior_area_chairs_id())
                    edge_writers.append(venue.get_senior_area_chairs_id(number=paper_number))
                    edge_signatures.append(venue.get_senior_area_chairs_id(number='.*'))
                if venue.use_area_chairs:
                    edge_invitees.append(venue.get_area_chairs_id())
                    edge_writers.append(venue.get_area_chairs_id(number=paper_number))
                    edge_signatures.append(venue.get_area_chairs_id(number='.*', anon=True))

                edge_nonreaders = [venue.get_authors_id(number=paper_number)]

        if self.is_area_chair:
            if venue.use_senior_area_chairs:
                edge_readers.append(venue.get_senior_area_chairs_id(number=paper_number))
                invitation_readers.append(venue.get_senior_area_chairs_id())

            if is_assignment_invitation:
                invitation_readers.append(venue.get_area_chairs_id())
                if self.venue.use_senior_area_chairs:
                    edge_invitees.append(venue.get_senior_area_chairs_id())
                    edge_writers.append(venue.get_senior_area_chairs_id(number=paper_number))
                    edge_signatures.append(venue.get_senior_area_chairs_id(number='.*'))

                edge_nonreaders = [venue.get_authors_id(number=paper_number)]

        if self.is_ethics_reviewer:
            if venue.use_ethics_chairs:
                edge_readers.append(venue.get_ethics_chairs_id())
                invitation_readers.append(venue.get_ethics_chairs_id())

            if is_assignment_invitation:
                if venue.use_ethics_chairs:
                    edge_invitees.append(venue.get_ethics_chairs_id())
                    edge_writers.append(venue.get_ethics_chairs_id())
                    edge_signatures.append(venue.get_ethics_chairs_id())

                edge_nonreaders = [venue.get_authors_id(number=paper_number)]

        #append tail to readers
        edge_readers.append('${2/tail}')

        edge_head = {
            'param': {
                'type': 'note',
                'withInvitation': venue.get_submission_id()
            }
        }
        if assignment_or_proposed:
            edge_head = {
                'param': {
                    'type': 'note',
                    'withVenueid': venue.get_submission_venue_id()
                }
            }
        edge_weight = {
            'param': {
                'minimum': -1
            }
        }
        edge_label = {
            'param': {
                'regex': '.*',
                'optional': True
            }
        }

        if venue.get_custom_max_papers_id(self.match_group.id) == edge_id:
            edge_head = {
                'param': {
                    'type': 'group',
                    'const': self.match_group.id
                }
            }

            edge_weight = {
                'param': {
                    'enum': [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
                }
            }
            edge_label = None

        if self.alternate_matching_group:
            edge_head = {
                'param': {
                    'type': 'profile',
                    'inGroup': self.alternate_matching_group
                }
            }

            edge_readers.append('${2/head}')
            edge_nonreaders = []

        edge_tail = {
            'param': {
                'type': 'profile',
                'inGroup': self.match_group.id
            }
        }

        if any_tail:
            edge_tail = {
                'param': {
                    'type': 'profile',
                    'regex': '~.*|.+@.+'
                }
            }
            edge_writers = [venue_id]

        if default_label and edge_label:
            edge_label['param']['default'] = default_label

        invitation = Invitation(
            id = edge_id,
            invitees = edge_invitees,
            readers = invitation_readers,
            writers = [venue_id],
            signatures = [venue_id],
            edge = {
                'id': {
                    'param': {
                        'withInvitation': edge_id,
                        'optional': True
                    }
                },
                'ddate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'cdate': {
                    'param': {
                        'range': [ 0, 9999999999999 ],
                        'optional': True,
                        'deletable': True
                    }
                },
                'readers':  edge_readers,
                'nonreaders': edge_nonreaders,
                'writers': edge_writers,
                'signatures': {
                    'param': { 
                        'regex': '|'.join(edge_signatures),
                        'default': [venue.get_program_chairs_id()]
                    }
                },
                'head': edge_head,
                'tail': edge_tail,
                'weight': edge_weight
            }
        )
        if edge_label:
            invitation.edge['label'] = edge_label

        invitation = self.venue.invitation_builder.save_invitation(invitation, replacement=True)
        return invitation

    def _build_conflicts(self, submissions, user_profiles, get_profile_info, compute_conflicts_n_years):
        if self.alternate_matching_group:
            other_matching_group = self.client.get_group(self.alternate_matching_group)
            other_matching_profiles = tools.get_profiles(self.client, other_matching_group.members)
            return self._build_profile_conflicts(other_matching_profiles, user_profiles, compute_conflicts_n_years)
        return self._build_note_conflicts(submissions, user_profiles, get_profile_info, compute_conflicts_n_years)

    def _build_note_conflicts(self, submissions, user_profiles, get_profile_info, compute_conflicts_n_years):
        invitation = self._create_edge_invitation(self.venue.get_conflict_score_id(self.match_group.id))
        invitation_id = invitation.id
        # Get profile info from the match group
        info_function = tools.info_function_builder(get_profile_info)
        user_profiles_info = [info_function(p, compute_conflicts_n_years) for p in user_profiles]
        # Get profile info from all the authors
        all_authorids = []
        for submission in submissions:
            authorids = submission.content['authorids']['value']
            all_authorids = all_authorids + authorids

        author_profile_by_id = tools.get_profiles(self.client, list(set(all_authorids)), with_publications=True, as_dict=True)

        ## for AC conflicts, check SAC conflicts too
        sac_user_info_by_id = {}
        if self.is_area_chair:
            sacs_by_ac =  { g['id']['head']: [v['tail'] for v in g['values']] for g in self.client.get_grouped_edges(invitation=self.venue.get_assignment_id(self.venue.get_senior_area_chairs_id()), groupby='head', select=None)}
            if sacs_by_ac:
                sac_user_profiles = openreview.tools.get_profiles(self.client, self.client.get_group(self.venue.get_senior_area_chairs_id()).members, with_publications=True)
                if self.sac_profile_info:
                    info_funcion = tools.info_function_builder(self.sac_profile_info)
                    sac_user_info_by_id = { p.id: info_funcion(p, self.sac_n_years, self.venue.get_submission_venue_id()) for p in sac_user_profiles }
                else:
                    sac_user_info_by_id = { p.id: info_function(p, compute_conflicts_n_years) for p in sac_user_profiles }
        edges = []

        for submission in tqdm(submissions, total=len(submissions), desc='_build_conflicts'):
            # Get author profiles
            authorids = submission.content['authorids']['value']

            # Extract domains from each authorprofile
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

                ## Transfer SAC conflicts
                if len(conflicts) == 0 and self.is_area_chair:
                    assigned_sacs = sacs_by_ac.get(user_info['id'], [])
                    for sac in assigned_sacs:
                        sac_info = sac_user_info_by_id.get(sac)
                        if sac_info:
                            conflicts.update(author_domains.intersection(sac_info['domains']))
                            conflicts.update(author_relations.intersection(sac_info['emails']))
                            conflicts.update(author_emails.intersection(sac_info['relations']))
                            conflicts.update(author_emails.intersection(sac_info['emails']))
                            conflicts.update(author_publications.intersection(sac_info['publications']))        

                if conflicts:
                    edges.append(Edge(
                        invitation=invitation_id,
                        head=submission.id,
                        tail=user_info['id'],
                        weight=-1,
                        label='Conflict',
                        readers=self._get_edge_readers(tail=user_info['id']),
                        writers=[self.venue.id],
                        signatures=[self.venue.id]
                    ))

        ## Delete previous conflicts
        self.client.delete_edges(invitation_id, wait_to_finish=True)

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)

        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation_id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of Conflict edges! Scores found: {0}, Edges posted: {1}'.format(len(edges), edges_posted))
        return invitation

    def _build_profile_conflicts(self, head_profiles, user_profiles, compute_conflicts_n_years):
        
        invitation = self._create_edge_invitation(self.venue.get_conflict_score_id(self.match_group.id))
        invitation_id = invitation.id
        # Get profile info from the match group
        info_function = openreview.tools.info_function_builder(openreview.tools.get_profile_info)
        user_profiles_info = [info_function(p, compute_conflicts_n_years) for p in user_profiles]
        head_profiles_info = [info_function(p, compute_conflicts_n_years) for p in head_profiles]

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
                        invitation=invitation_id,
                        head=head_profile_info['id'],
                        tail=user_info['id'],
                        weight=-1,
                        label='Conflict',
                        readers=self._get_edge_readers(tail=user_info['id']),
                        writers=[self.venue.id],
                        signatures=[self.venue.id]
                    ))

        ## Delete previous conflicts
        self.client.delete_edges(invitation_id, wait_to_finish=True)

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)

        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation_id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of Conflict edges! Scores found: {0}, Edges posted: {1}'.format(len(edges), edges_posted))
        return invitation

    def _build_custom_max_papers(self, user_profiles):
        invitation=self._create_edge_invitation(self.venue.get_custom_max_papers_id(self.match_group.id))
        invitation_id = invitation.id
        current_custom_max_edges={ e['id']['tail']: Edge.from_json(e['values'][0]) for e in self.client.get_grouped_edges(invitation=invitation_id, groupby='tail', select=None)}

        reduced_loads = {}
        reduced_load_notes = self.client.get_all_notes(invitation=self.venue.get_recruitment_id(self.match_group.id), sort='tcdate:asc')
        for note in tqdm(reduced_load_notes, desc='getting reduced load notes'):
            if 'reduced_load' in note.content:
                reduced_loads[note.content['user']['value']] = note.content['reduced_load']['value']

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
                        invitation=invitation_id,
                        readers=self._get_edge_readers(user_profile.id),
                        writers=[self.venue.id],
                        signatures=[self.venue.id],
                        weight=review_capacity
                    )
                    edges.append(edge)


        openreview.tools.post_bulk_edges(client=self.client, edges=edges)

        return invitation

    def _build_scores_from_file(self, score_invitation_id, score_file, submissions):
        if self.alternate_matching_group:
            return self._build_profile_scores(score_invitation_id, score_file=score_file)
        scores = []
        with open(score_file) as file_handle:
            scores = [row for row in csv.reader(file_handle)]
        return self._build_note_scores(score_invitation_id, scores, submissions)

    def _build_scores_from_stream(self, score_invitation_id, scores_stream, submissions):
        scores = [input_line.split(',') for input_line in scores_stream.decode().strip().split('\n')]
        if self.alternate_matching_group:
            return self._build_profile_scores(score_invitation_id, scores=scores)
        return self._build_note_scores(score_invitation_id, scores, submissions)

    def _build_profile_scores(self, score_invitation_id, score_file=None, scores=None):

        invitation = self._create_edge_invitation(score_invitation_id)
        invitation_id = invitation.id
        edges = []

        # Validate and select scores
        if not scores and not score_file:
            raise openreview.OpenReviewException('No profile scores provided')
        if scores:
            score_handle = scores
        elif score_file:
            score_handle = csv.reader(open(score_file))

        for row in tqdm(score_handle, desc='_build_scores'):

            score = str(max(round(float(row[2]), 4), 0))
            edges.append(Edge(
                    invitation=invitation_id,
                    head=row[0],
                    tail=row[1],
                    weight=float(score),
                    readers=self._get_edge_readers(tail=row[1]),
                    writers=[self.venue.id],
                    signatures=[self.venue.id]
                ))

        ## Delete previous scores
        self.client.delete_edges(invitation_id, wait_to_finish=True)

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)
        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation_id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of {0} edges! Input file:{1}, Scores found: {2}, Edges posted: {3}'.format(score_invitation_id, score_file, len(edges), edges_posted))
        return invitation

    def _build_note_scores(self, score_invitation_id, scores, submissions):

        invitation = self._create_edge_invitation(score_invitation_id)
        invitation_id = invitation.id

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
                        invitation=invitation_id,
                        head=paper_note_id,
                        tail=profile_id,
                        weight=float(score),
                        readers=self._get_edge_readers(tail=profile_id),
                        # nonreaders=[self.venue.get_authors_id(number=paper_number)],
                        writers=[self.venue.id],
                        signatures=[self.venue.id]
                    ))
                else:
                    deleted_papers.add(paper_note_id)

        print('deleted papers', deleted_papers)

        ## Delete previous scores
        self.client.delete_edges(invitation_id, wait_to_finish=True)

        openreview.tools.post_bulk_edges(client=self.client, edges=edges)
        # Perform sanity check
        edges_posted = self.client.get_edges_count(invitation=invitation_id)
        if edges_posted < len(edges):
            raise openreview.OpenReviewException('Failed during bulk post of {0} edges! Input file:{1}, Scores found: {2}, Edges posted: {3}'.format(score_invitation_id, score_file, len(edges), edges_posted))
        return invitation

    def _compute_scores(self, score_invitation_id, submissions):

        venue = self.venue
        client = self.client
        matching_status = {
            'no_profiles': [],
            'no_publications': []
        }

        try:
            job_id = client.request_expertise(
                name=venue.get_short_name(),
                group_id=self.match_group.id,
                venue_id=venue.get_submission_venue_id(),
                alternate_match_group=self.alternate_matching_group,
                expertise_selection_id=venue.get_expertise_selection_id(self.match_group.id),
                model='specter+mfr'
            )
            status = ''
            call_count = 0
            while 'Completed' not in status and 'Error' not in status:
                if call_count == 1440: ## one day to wait the completion or trigger a timeout
                    break
                time.sleep(60)
                status_response = client.get_expertise_status(job_id['jobId'])
                status = status_response.get('status')
                desc = status_response.get('description')
                call_count += 1
            if 'Completed' in status:
                result = client.get_expertise_results(job_id['jobId'])
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

    def _build_config_invitation(self, scores_specification):
        venue = self.venue

        config_inv = Invitation(
            id = '{}/-/{}'.format(self.match_group.id, 'Assignment_Configuration'),
            invitees = [venue.id, venue.support_user],
            signatures = [venue.id],
            readers = [venue.id],
            writers = [venue.id],
            edit = {
                'signatures': [venue.id],
                'readers': [venue.id],
                'writers': [venue.id],
                'note': {
                    'id': {
                        'param': {
                            'withInvitation': '{}/-/{}'.format(self.match_group.id, 'Assignment_Configuration'),
                            'optional': True
                        }
                    },
                    'ddate': {
                        # 'type': 'date',
                        'param': {
                            'range': [ 0, 9999999999999 ],
                            'optional': True,
                            'deletable': True
                        }
                    },
                    'signatures': [venue.id],
                    'readers': [venue.id],
                    'writers': [venue.id],
                    'content': {
                        'title': {
                            'order': 1,
                            'description': 'Title of the configuration.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '.{1,250}'
                                }
                            }
                        },
                        'user_demand': {
                            'order': 2,
                            'description': 'Number of users that can review a paper',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '[0-9]+'
                                }
                            }
                        },
                        'max_papers': {
                            'order': 3,
                            'description': 'Max number of reviews a user has to do',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '[0-9]+'
                                }
                            }
                        },
                        'min_papers': {
                            'order': 4,
                            'description': 'Min number of reviews a user should do',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '[0-9]+'
                                }
                            }
                        },
                        'alternates': {
                            'order': 5,
                            'description': 'The number of alternate reviewers to save (per-paper)',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '[0-9]+'
                                }
                            }
                        },
                        'paper_invitation': {
                            'order': 6,
                            'description': 'Invitation to get the paper metadata or Group id to get the users to be matched',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': self.alternate_matching_group if self.alternate_matching_group else venue.get_submission_id() + '.*',
                                    'default': self.alternate_matching_group if self.alternate_matching_group else f'{venue.get_submission_id()}&content.venueid={venue.get_submission_venue_id()}',
                                }
                            }
                        },
                        'match_group': {
                            'order': 7,
                            'description': 'Group id containing users to be matched',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '{}/.*'.format(venue.id),
                                    'default': self.match_group.id,
                                }
                            }
                        },
                        'scores_specification': {
                            'order': 8,
                            'description': 'Manually entered JSON score specification',
                            'value': {
                                'param': {
                                    'type': 'json',
                                    'default': scores_specification,
                                    'optional': True
                                }
                            }
                        },
                        'aggregate_score_invitation': {
                            'order': 9,
                            'description': 'Invitation to store aggregated scores',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '{}/.*'.format(venue.id),
                                    'default': self._get_edge_invitation_id('Aggregate_Score'),
                                    'hidden': True
                                }
                            }
                        },
                        'conflicts_invitation': {
                            'order': 10,
                            'description': 'Invitation to store conflict scores',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '{}/.*'.format(venue.id),
                                    'default': venue.get_conflict_score_id(self.match_group.id),
                                }
                            }
                        },
                        'assignment_invitation': {
                            'order': 11,
                            'description': 'Invitation to store paper user assignments',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': venue.get_assignment_id(self.match_group.id),
                                    'hidden': True
                                }
                            }
                        },
                        'deployed_assignment_invitation': {
                            'order': 12,
                            'description': 'Invitation to store deployed paper user assignments',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': venue.get_assignment_id(self.match_group.id, deployed=True),
                                    'hidden': True
                                }
                            }
                        },
                        'invite_assignment_invitation': {
                            'order': 13,
                            'description': 'Invitation used to invite external or emergency reviewers',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const': venue.get_assignment_id(self.match_group.id, invite=True),
                                    'hidden': True
                                }
                            }
                        },
                        'custom_user_demand_invitation': {
                            'order': 14,
                            'description': 'Invitation to store custom number of users required by papers',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex': '{}/.*/-/Custom_User_Demands$'.format(venue.id),
                                    'default': '{}/-/Custom_User_Demands'.format(self.match_group.id),
                                    'optional': True
                                }
                            }
                        },
                        'custom_max_papers_invitation': {
                            'order': 15,
                            'description': 'Invitation to store custom max number of papers that can be assigned to reviewers',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex':  '{}/.*/-/Custom_Max_Papers$'.format(venue.id),
                                    'default': venue.get_custom_max_papers_id(self.match_group.id),
                                    'optional': True
                                }
                            }
                        },
                        'config_invitation': {
                            'order': 16,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'const':  self._get_edge_invitation_id('Assignment_Configuration'),
                                    'hidden': True
                                }
                            }
                        },
                        'solver': {
                            'order': 17,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': ['MinMax', 'FairFlow', 'Randomized', 'FairSequence'],
                                    'input': 'radio'
                                }
                            }
                        },
                        'status': {
                            'order': 18,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum': [
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
                                    'input': 'select',
                                    'default': 'Initialized'
                                }
                            }
                        },
                        'error_message': {
                            'order': 19,
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex':  '.*',
                                    'optional': True,
                                    'hidden': True
                                }
                            }
                        },
                        'allow_zero_score_assignments': {
                            'order': 20,
                            'description': 'Select "No" only if you do not want to allow assignments with 0 scores. Note that if there are any users without publications, you need to select "Yes" in order to run a paper matching.',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'enum':  ['Yes', 'No'],
                                    'input': 'radio',
                                    'optional': True,
                                    'default': 'Yes'
                                }
                            }
                        },
                        'randomized_probability_limits': {
                            'order': 21,
                            'description': 'Enter the probability limits if the selected solver is Randomized',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex':  r'[-+]?[0-9]*\.?[0-9]*',
                                    'optional': True,
                                    'default': '1'
                                }
                            }
                        },
                        'randomized_fraction_of_opt': {
                            'order': 22,
                            'description': 'result of randomized assignment',
                            'value': {
                                'param': {
                                    'type': 'string',
                                    'regex':  r'[-+]?[0-9]*\.?[0-9]*',
                                    'optional': True,
                                    'default': '',
                                    'hidden': True
                                }
                            }
                        }
                    }
                }
            }
        )

        invitation = venue.invitation_builder.save_invitation(config_inv)

    def setup(self, compute_affinity_scores=False, compute_conflicts=False, compute_conflicts_n_years=None):

        venue = self.venue
        client = self.client

        matching_status = {
            'no_profiles': [],
            'no_publications': []
        }

        # The reviewers are all emails so convert to tilde ids
        self.match_group = openreview.tools.replace_members_with_ids(client, self.match_group)
        matching_status['no_profiles'] = [member for member in self.match_group.members if '~' not in member]
        if matching_status['no_profiles']:
            print(
                'WARNING: not all reviewers have been converted to profile IDs.',
                'Members without profiles will not have metadata created.')

        user_profiles = openreview.tools.get_profiles(client, self.match_group.members, with_publications=compute_conflicts)

        submissions = venue.get_submissions(sort='number:asc')

        if not self.match_group.members:
            raise openreview.OpenReviewException(f'The match group is empty: {self.match_group.id}')
        if self.alternate_matching_group:
            other_matching_group = self.client.get_group(self.alternate_matching_group)
            if not other_matching_group.members:
                raise openreview.OpenReviewException(f'The alternate match group is empty: {self.alternate_matching_group}')
        elif not submissions:
            raise openreview.OpenReviewException('Submissions not found.')

        type_affinity_scores = type(compute_affinity_scores)

        if type_affinity_scores == str:
            self._build_scores_from_file(
                venue.get_affinity_score_id(self.match_group.id),
                compute_affinity_scores,
                submissions
            )

        if type_affinity_scores == bytes:
            self._build_scores_from_stream(
                venue.get_affinity_score_id(self.match_group.id),
                compute_affinity_scores,
                submissions
            )

        if compute_affinity_scores == True:
            invitation, matching_status = self._compute_scores(
                venue.get_affinity_score_id(self.match_group.id),
                submissions
            )

        if compute_conflicts:
            self._build_conflicts(submissions, user_profiles, openreview.tools.get_neurips_profile_info if compute_conflicts == 'NeurIPS' else openreview.tools.get_profile_info, compute_conflicts_n_years)


        if venue.automatic_reviewer_assignment:
            invitation = self._create_edge_invitation(venue.get_assignment_id(self.match_group.id))
            
            if not self.is_senior_area_chair:
                with open(os.path.join(os.path.dirname(__file__), 'process/proposed_assignment_pre_process.js')) as f:
                    content = f.read()
                    invitation.content = { 'committee_name': { 'value': self.get_committee_name() }}
                    invitation.preprocess = content
                    venue.invitation_builder.save_invitation(invitation)

            self._create_edge_invitation(self._get_edge_invitation_id('Aggregate_Score'))
            score_spec = {}
            
            invitation = openreview.tools.get_invitation(self.client, venue.get_affinity_score_id(self.match_group.id))
            if invitation:
                score_spec[invitation.id] = {
                    'weight': 1,
                    'default': 0
                }

            invitation = openreview.tools.get_invitation(self.client, venue.get_bid_id(self.match_group.id))
            if invitation:
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

            invitation = openreview.tools.get_invitation(self.client, venue.get_recommendation_id(self.match_group.id))
            if invitation:
                score_spec[invitation.id] = {
                    'weight': 1,
                    'default': 0
                }

            self._build_config_invitation(score_spec)            
        else:
            venue.invitation_builder.set_assignment_invitation(self.match_group.id)

        self._build_custom_max_papers(user_profiles)
        self._create_edge_invitation(self._get_edge_invitation_id('Custom_User_Demands'))
        self.venue.update_conflict_policies(self.match_group.id, compute_conflicts, compute_conflicts_n_years)

        return matching_status

    def setup_invite_assignment(self, hash_seed, assignment_title=None, due_date=None, invitation_labels={}, invited_committee_name='External_Reviewers', email_template=None, proposed=False):
        venue = self.venue

        invite_label=invitation_labels.get('Invite', 'Invitation Sent')
        invited_label=invitation_labels.get('Invited', 'Invitation Sent')
        accepted_label=invitation_labels.get('Accepted', 'Accepted')
        declined_label=invitation_labels.get('Declined', 'Declined')

        recruitment_invitation_id=venue.get_invitation_id('Proposed_Assignment_Recruitment' if assignment_title else 'Assignment_Recruitment', prefix=self.match_group.id)
        invitation=self._create_edge_invitation(venue.get_assignment_id(self.match_group.id, invite=True), any_tail=True, default_label=invite_label)

        invitation_content = {
            'match_group': { 'value':  self.match_group.id },
            'assignment_invitation_id': { 'value': venue.get_assignment_id(self.match_group.id) if assignment_title else venue.get_assignment_id(self.match_group.id, deployed=True)},
            'conflict_invitation_id': { 'value': venue.get_conflict_score_id(self.match_group.id) },
            'assignment_label': { 'value': assignment_title } if assignment_title else { 'delete': True },
            'invite_label': { 'value': invite_label },
            'invited_label': { 'value': invited_label },
            'recruitment_invitation_id': { 'value': recruitment_invitation_id },
            'committee_invited_id': { 'value': venue.get_committee_id(name=invited_committee_name + '/Invited') },
            'paper_reviewer_invited_id': { 'value': venue.get_committee_id(name=invited_committee_name + '/Invited', number='{number}') if assignment_title else ''},
            'hash_seed': { 'value': hash_seed, 'readers': [ venue.venue_id ]},
            'email_template': { 'value': email_template if email_template else ''}
        }

        # set invite assignment invitation
        pre_process_content = venue.invitation_builder.get_process_content('process/invite_assignment_pre_process.js')
        post_process_content = venue.invitation_builder.get_process_content('process/invite_assignment_post_process.py')

        invitation.preprocess = pre_process_content
        invitation.process = post_process_content
        invitation.content = invitation_content
        invitation.edit['label'] = {
            'param': {
                'enum': [
                    invited_label,
                    accepted_label,
                    declined_label + '.*',
                    'Pending Sign Up',
                    'Conflict Detected'
                ],
                'optional': True,
                'default': invited_label
            }
        }
        invitation.minReplies = 1
        invitation.maxReplies = 1
        invitation.signatures = [venue.get_program_chairs_id()]
        invite_assignment_invitation=venue.invitation_builder.save_invitation(invitation, replacement=True)

        # set assignment recruitment invitation
        invitation = venue.invitation_builder.set_paper_recruitment_invitation(recruitment_invitation_id,
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

        #To-Do
        ## Only for reviewers, allow ACs and SACs to review the proposed assignments
        if self.match_group.id == venue.get_reviewers_id() and not proposed:
            venue.group_builder.set_external_reviewer_recruitment_groups(name=invited_committee_name, create_paper_groups=True if assignment_title else False)
            if assignment_title:
                invitation=self.client.get_invitation(venue.get_assignment_id(self.match_group.id))
                invitation.duedate=tools.datetime_millis(due_date)
                invitation.expdate=tools.datetime_millis(due_date + datetime.timedelta(minutes= 30)) if due_date else None
                venue.invitation_builder.save_invitation(invitation, replacement=True)
            #     invitation = self.conference.webfield_builder.set_reviewer_proposed_assignment_page(self.conference, invitation, assignment_title, invite_assignment_invitation)

        return invite_assignment_invitation

    def deploy_assignments(self, assignment_title, overwrite):

        venue = self.venue
        client = self.client

        committee_id=self.match_group.id
        role_name = committee_id.split('/')[-1]
        review_name = 'Official_Review'
        reviewer_name = venue.reviewers_name
        if role_name in venue.area_chair_roles:
            reviewer_name = venue.area_chairs_name
            review_name = 'Meta_Review'

        papers = venue.get_submissions()
        reviews = client.get_notes(invitation=venue.get_invitation_id(review_name, number='.*'), limit=1)
        proposed_assignment_edges =  { g['id']['head']: g['values'] for g in client.get_grouped_edges(invitation=venue.get_assignment_id(self.match_group.id),
            label=assignment_title, groupby='head', select=None)}
        assignment_invitation_id = venue.get_assignment_id(self.match_group.id, deployed=True)
        current_assignment_edges =  { g['id']['head']: g['values'] for g in client.get_grouped_edges(invitation=assignment_invitation_id, groupby='head', select=None)}

        sac_assignment_edges =  { g['id']['head']: g['values'] for g in client.get_grouped_edges(invitation=venue.get_assignment_id(venue.get_senior_area_chairs_id(), deployed=True), groupby='head', select=None)}

        if overwrite:
            if reviews:
                raise openreview.OpenReviewException('Can not overwrite assignments when there are reviews posted.')
            ## Remove the members from the groups based on the current assignments
            for paper in tqdm(papers, total=len(papers)):
                if paper.id in current_assignment_edges:
                    paper_committee_id = venue.get_committee_id(name=reviewer_name, number=paper.number)
                    current_edges=current_assignment_edges[paper.id]
                    for current_edge in current_edges:
                        client.remove_members_from_group(paper_committee_id, current_edge['tail'])
                else:
                    print('assignment not found', paper.id)
            ## Delete current assignment edges with a ddate in case we need to do rollback
            client.delete_edges(invitation=assignment_invitation_id, wait_to_finish=True, soft_delete=True)

        def process_paper_assignments(paper):
            paper_assignment_edges = []
            if paper.id in proposed_assignment_edges:
                paper_committee_id = venue.get_committee_id(name=reviewer_name, number=paper.number)
                proposed_edges=proposed_assignment_edges[paper.id]
                assigned_users = []
                for proposed_edge in proposed_edges:
                    assigned_user = proposed_edge['tail']
                    if self.is_area_chair and sac_assignment_edges:
                        sac_assignments = sac_assignment_edges.get(assigned_user, [])
                        for sac_assignment in sac_assignments:
                            assigned_sac = sac_assignment['tail']
                            sac_group_id = venue.get_senior_area_chairs_id(number=paper.number)
                            client.post_group_edit(
                                invitation = venue.get_meta_invitation_id(),
                                readers = [venue.venue_id],
                                writers = [venue.venue_id],
                                signatures = [venue.venue_id],
                                group = openreview.api.Group(
                                    id = sac_group_id,
                                    members = [assigned_sac]
                                )
                            )
                    paper_assignment_edges.append(Edge(
                        invitation=assignment_invitation_id,
                        head=paper.id,
                        tail=assigned_user,
                        readers=proposed_edge['readers'],
                        nonreaders=proposed_edge.get('nonreaders'),
                        writers=proposed_edge['writers'],
                        signatures=proposed_edge['signatures'],
                        weight=proposed_edge.get('weight')
                    ))
                    assigned_users.append(assigned_user)
                client.add_members_to_group(paper_committee_id, assigned_users)
                return paper_assignment_edges
            else:
                print('assignment not found', paper.id)
                return []

        assignment_edges = reduce(concat,tools.concurrent_requests(process_paper_assignments, papers))

        print('Posting assignment edges', len(assignment_edges))
        openreview.tools.post_bulk_edges(client=client, edges=assignment_edges)

    def deploy_sac_assignments(self, assignment_title, overwrite):

        client = self.client
        venue = self.venue

        print('deploy_sac_assignments', assignment_title)

        proposed_assignment_edges =  { g['id']['head']: g['values'] for g in client.get_grouped_edges(invitation=venue.get_assignment_id(self.match_group.id),
            label=assignment_title, groupby='head', select=None)}
        assignment_edges = []
        assignment_invitation_id = venue.get_assignment_id(self.match_group.id, deployed=True)

        for head, sac_assignments in proposed_assignment_edges.items():
            for sac_assignment in sac_assignments:
                assignment_edges.append(Edge(
                    invitation=assignment_invitation_id,
                    head=head,
                    tail=sac_assignment['tail'],
                    readers=sac_assignment['readers'],
                    nonreaders=sac_assignment.get('nonreaders'),
                    writers=sac_assignment['writers'],
                    signatures=sac_assignment['signatures'],
                    weight=sac_assignment.get('weight')
                ))

        print('Posting assignments edges', len(assignment_edges))
        openreview.tools.post_bulk_edges(client=client, edges=assignment_edges)

    def deploy(self, assignment_title, overwrite=False, enable_reviewer_reassignment=False):

        self.venue.invitation_builder.set_assignment_invitation(self.match_group.id)
        recruitment_invitation_id=self.venue.get_invitation_id('Proposed_Assignment_Recruitment', prefix=self.match_group.id)
        self.venue.invitation_builder.expire_invitation(recruitment_invitation_id)
        self.venue.invitation_builder.expire_invitation(self.venue.get_assignment_id(self.match_group.id))
        
        ## Deploy assignments creating groups and assignment edges
        if self.match_group.id == self.venue.get_senior_area_chairs_id():
            self.deploy_sac_assignments(assignment_title, overwrite)
        else:
            self.deploy_assignments(assignment_title, overwrite)

        if self.match_group.id == self.venue.get_reviewers_id() and enable_reviewer_reassignment:
            hash_seed=''.join(random.choices(string.ascii_uppercase + string.digits, k = 8))
            self.setup_invite_assignment(hash_seed=hash_seed, invited_committee_name=f'''Emergency_{self.venue.reviewers_name}''')
