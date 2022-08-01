import os
import openreview
from openreview.api import Edge
from openreview.api import Invitation

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

    def _create_edge_invitation(self, edge_id, any_tail=False, default_label=None):

        venue = self.venue
        venue_id = venue.venue_id
        
        is_assignment_invitation=edge_id.endswith('Assignment') or edge_id.endswith('Aggregate_Score')
        paper_number = '${{2/head}/number}'

        paper_num_signatures = '${{1/head}/number}'

        edge_invitees = [venue_id, venue.support_user]
        edge_readers = [venue_id]
        invitation_readers = [venue_id]
        edge_writers = [venue_id]
        edge_signatures = [venue_id + '$', venue.get_program_chairs_id()]
        edge_nonreaders = [venue.get_authors_id(number=paper_number)]

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
                    edge_signatures.append(venue.get_senior_area_chairs_id(number=paper_num_signatures))
                if venue.use_area_chairs:
                    edge_invitees.append(venue.get_area_chairs_id())
                    edge_writers.append(venue.get_area_chairs_id(number=paper_number))
                    edge_signatures.append(venue.get_area_chairs_id(number=paper_num_signatures))

        if self.is_area_chair:
            if venue.use_senior_area_chairs:
                edge_readers.append(venue.get_senior_area_chairs_id(number=paper_number))
                invitation_readers.append(venue.get_senior_area_chairs_id())

            if is_assignment_invitation:
                if self.conference.use_senior_area_chairs:
                    edge_invitees.append(venue.get_senior_area_chairs_id())
                    edge_writers.append(venue.get_senior_area_chairs_id(number=paper_number))
                    edge_signatures.append(venue.get_senior_area_chairs_id(number=paper_num_signatures))

        if self.is_ethics_reviewer:
            if venue.use_ethics_chairs:
                edge_readers.append(venue.get_ethics_chairs_id())
                invitation_readers.append(venue.get_ethics_chairs_id())

            if is_assignment_invitation:
                if venue.use_ethics_chairs:
                    edge_invitees.append(venue.get_ethics_chairs_id())
                    edge_writers.append(venue.get_ethics_chairs_id())
                    edge_signatures.append(venue.get_ethics_chairs_id())

        #append tail to readers
        edge_readers.append('${2/tail}')

        edge_head = {
            'param': {
                'type': 'note',
                'withInvitation': venue.submission_stage.get_submission_id(venue)
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

            edge_readers.append('${{2/head}}')

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
                        # 'type': 'date',
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

        invitation = self.venue.invitation_builder.save_invitation(invitation)
        return invitation

    def setup(self, compute_affinity_scores=False, compute_conflicts=False):

        venue = self.venue
        client = self.client

        score_spec = {}
        matching_status = {
            'no_profiles': [],
            'no_publications': []
        }

        try:
            invitation = client.get_invitation(venue.get_bid_id(self.match_group.id))
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
        self.match_group = openreview.tools.replace_members_with_ids(client, self.match_group)
        matching_status['no_profiles'] = [member for member in self.match_group.members if '~' not in member]
        if matching_status['no_profiles']:
            print(
                'WARNING: not all reviewers have been converted to profile IDs.',
                'Members without profiles will not have metadata created.')

        user_profiles = openreview.tools.get_profiles(client, self.match_group.members, with_publications=compute_conflicts)

        invitation = self._create_edge_invitation(venue.get_paper_assignment_id(self.match_group.id))
        
        ## is there better way to do this?
        if not self.is_senior_area_chair:
            invitation = invitation['invitation']
            with open(os.path.join(os.path.dirname(__file__), 'process/proposed_assignment_pre_process.py')) as f:
                content = f.read()
                content = content.replace("CUSTOM_MAX_PAPERS_INVITATION_ID = ''", "CUSTOM_MAX_PAPERS_INVITATION_ID = '" + venue.get_custom_max_papers_id(self.match_group.id) + "'")
                invitation['preprocess']=content
                venue.invitation_builder.save_invitation(Invitation.from_json(invitation))

        self._create_edge_invitation(venue.get_paper_assignment_id(self.match_group.id, deployed=True))
