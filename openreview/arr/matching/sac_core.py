from __future__ import annotations
import json
import openreview
import logging
import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from openreview.stages.arr_content import arr_tracks
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional
from copy import deepcopy
from collections import Counter

from sac_utils import (
    multiple_sac_tracks_to_single_track,
    rebalance_sacs_across_tracks,
    assign_acs_to_sac,
    compute_priority_track_load_plan,
    merge_sac_tracks_with_volunteers,
)
from edge_utils import delete_edges_with_polling

from constants import (
    DEFAULT_AC_MATCHING_CONFIG,
    DEFAULT_SAC_MATCHING_CONFIG,
)


def delete_edges_with_polling(
    client: openreview.api.OpenReviewClient,
    *,
    invitation: str,
    id: Optional[str] = None,
    label: Optional[str] = None,
    head: Optional[str] = None,
    tail: Optional[str] = None,
    domain: Optional[str] = None,
    soft_delete: bool = False,
    poll_interval_seconds: int = 30,
    max_polls: int = 40,
) -> None:
    """
    Trigger asynchronous edge deletion and poll until the matching edges disappear.

    Parameters mirror ``OpenReviewClient.delete_edges`` with two extra controls:
    ``poll_interval_seconds`` and ``max_polls``. The function raises if the edges do
    not disappear within ``poll_interval_seconds * max_polls`` seconds.
    """

    if not invitation:
        raise ValueError("invitation is required to delete edges")

    delete_filters = {
        "invitation": invitation,
    }
    if id:
        delete_filters["id"] = id
    if label:
        delete_filters["label"] = label
    if head:
        delete_filters["head"] = head
    if tail:
        delete_filters["tail"] = tail

    client.delete_edges(
        **delete_filters,
        wait_to_finish=False,
        soft_delete=soft_delete,
    )

    count_filters = delete_filters.copy()
    if domain:
        count_filters["domain"] = domain

    polls = 0
    while polls < max_polls:
        remaining = client.get_edges_count(**count_filters)
        print(f"Waiting for edges to delete, remaining: {remaining}")
        if remaining == 0:
            return
        time.sleep(poll_interval_seconds)
        polls += 1

    raise openreview.OpenReviewException(
        f"Timed out waiting for edges to delete after {poll_interval_seconds * max_polls} seconds "
        f"for invitation={invitation}, label={label}, head={head}, tail={tail}."
    )


@dataclass
class MatchingData:
    """
    Loads venue data from OpenReview needed for SAC/AC assignment

    Parameters
    ----------
    client : openreview.api.OpenReviewClient
    """

    # --- required inputs -------------------------------------------------- #
    client: openreview.api.OpenReviewClient
    venue_id: str
    exclude_sacs: set[str] | None = None
    # --- data containers (populated automatically) ------------------------ #
    track_fallback: Dict[str, List[str]] = field(init=False)
    data_dump: str = field(init=False, default=None)
    
    all_submissions: List[openreview.api.Note] = field(init=False)
    submissions: List[openreview.api.Note] = field(init=False)
    submissions_by_track: Dict[str, List[openreview.api.Note]] = field(init=False)
    submission_to_track: Dict[str, str] = field(init=False)

    sacs_profiles: List[openreview.Profile] = field(init=False)
    acs_profiles: List[openreview.Profile] = field(init=False)
    sacs: openreview.api.Group = field(init=False)
    acs: openreview.api.Group = field(init=False)
    name_to_id: Dict[str, str] = field(init=False)

    sac_reg: Dict[str, openreview.api.Note] = field(init=False)
    ac_reg: Dict[str, openreview.api.Note] = field(init=False)
    ac_loads: Dict[str, openreview.api.Note] = field(init=False)
    sac_to_tracks: Dict[str, List[str]] = field(init=False) ## Initial mapping from notes
    sac_priority_tracks: Dict[str, List[str]] = field(init=False) ## Single priority track per SAC when provided
    ac_to_tracks: Dict[str, List[str]] = field(init=False) ## Initial mapping from notes

    ac_cmp: Dict[str, int] = field(init=False)
    sac_cois: Dict[str, List[Dict[str, Any]]] = field(init=False)
    ac_cois: Dict[str, List[Dict[str, Any]]] = field(init=False)
    sac_aff: Dict[str, List[Dict[str, Any]]] = field(init=False) ## By tail

    ac_matching_config: Dict[str, Any] = field(init=False)
    sac_matching_config: Dict[str, Any] = field(init=False)
    priority_track_load_plan: Any = field(init=False, default=None)

    # ---------------------------------------------------------------------- #
    # life‑cycle hooks
    # ---------------------------------------------------------------------- #
    def __post_init__(self) -> None:
        logger = logging.getLogger(__name__)
        logger.debug("Fetching matching data")
        with open('arr_track_fallback.json', 'r') as f:
            self.track_fallback = json.load(f)

        self._populate_submissions(logger)
        self._populate_reviewers_and_tracks(logger)
        self._populate_edges(logger)
        self._populate_registration_and_load(logger)
        self._populate_matching_configs(logger)

        # Ensure committee-specific data only references active members
        self._enforce_committee_membership(logger)

        # Apply optional SAC exclusions globally
        self._apply_sac_exclusions(logger)

        logger.debug("Finished fetching matching data")

    # ---------------------------------------------------------------------- #
    # helper functions
    # ---------------------------------------------------------------------- #
    def _populate_submissions(self, logger: logging.Logger) -> None:
        """Fill `submissions` and `submissions_by_track`."""
        logger.debug("Populating submissions …")
        self.submissions = self.client.get_all_notes(
            content={ 'venueid': f"{self.venue_id}/Submission"}
        )

        self.all_submissions = self.client.get_all_notes(
            invitation=f"{self.venue_id}/-/Submission"
        )

        self.submissions_by_track = {
            track: [submission for submission in self.submissions if submission.content['research_area']['value'] == track]
            for track in arr_tracks
        }
        self.submission_to_track = {
            submission.id: submission.content['research_area']['value'] for submission in self.all_submissions
        }

    def _populate_reviewers_and_tracks(self, logger: logging.Logger) -> None:
        """Fill SAC/AC lists and their track mappings."""
        logger.debug("Populating reviewers and track mappings …")
        self.sacs = self.client.get_group(self.venue_id + '/Senior_Area_Chairs')
        self.acs = self.client.get_group(self.venue_id + '/Area_Chairs')

        self.sacs_profiles = openreview.tools.get_profiles(self.client, self.sacs.members)
        self.acs_profiles = openreview.tools.get_profiles(self.client, self.acs.members)

        all_profiles = self.sacs_profiles + self.acs_profiles
        self.name_to_id = {}
        for profile in all_profiles:
            for name_obj in profile.content.get('names', []):
                if 'username' in name_obj and len(name_obj['username']) > 0:
                    self.name_to_id[name_obj['username']] = profile.id

    def _populate_registration_and_load(self, logger: logging.Logger) -> None:
        """Fill registration info and load limits."""
        logger.debug("Populating registration forms and load limits …")
        sac_registration_notes = self.client.get_all_notes(
            invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Registration"
        )
        ac_registration_notes = self.client.get_all_notes(
            invitation=f"{self.venue_id}/Area_Chairs/-/Registration"
        )
        ac_load_notes = self.client.get_all_notes(
            invitation=f"{self.venue_id}/Area_Chairs/-/Max_Load_And_Unavailability_Request"
        )
        
        self.sac_reg = {
            self.name_to_id[note.signatures[0]]: note for note in sac_registration_notes if note.signatures[0] in self.name_to_id
        }
        self.ac_reg = {
            self.name_to_id[note.signatures[0]]: note for note in ac_registration_notes if note.signatures[0] in self.name_to_id
        }
        self.ac_loads = {
            self.name_to_id[note.signatures[0]]: note for note in ac_load_notes if note.signatures[0] in self.name_to_id
        }

        self.sac_to_tracks = {
            sac_id: sac_reg.content.get('research_area', {}).get('value', []) for sac_id, sac_reg in self.sac_reg.items()
        }
        # Priority track (single) if provided under content.priority_research_area
        self.sac_priority_tracks = {}
        for sac_id, sac_reg in self.sac_reg.items():
            raw = sac_reg.content.get('priority_research_area')
            val = None
            if raw is not None:
                if isinstance(raw, dict):
                    val = raw.get('value', None)
                else:
                    val = raw
            if isinstance(val, list):
                val = val[0] if val else None
            if isinstance(val, str) and val:
                self.sac_priority_tracks[sac_id] = [val]
            else:
                # Fallback: if missing, take the first declared research_area as the priority
                tracks = self.sac_to_tracks.get(sac_id, [])
                self.sac_priority_tracks[sac_id] = [tracks[0]] if tracks else []
        self.ac_to_tracks = {
            ac_id: ac_reg.content['research_area']['value'] for ac_id, ac_reg in self.ac_reg.items()
        }
        #print(f"ac_to_tracks: {json.dumps(self.ac_to_tracks, indent=4)}")

    def _populate_edges(self, logger: logging.Logger) -> None:
        """Fill COI and assignment dictionaries."""
        logger.debug("Populating conflicts of interest and assignments …")
        self.sac_cois = {
            group['id']['tail']: [e for e in group['values']] for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Conflict",
                groupby='tail'
            )
        }
        self.ac_cois = {
            group['id']['tail']: [e for e in group['values']] for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Area_Chairs/-/Conflict",
                groupby='tail'
            )
        }
        self.ac_cmp = {
            group['id']['tail']: int(group['values'][0]['weight']) for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Area_Chairs/-/Custom_Max_Papers",
                groupby='tail'
            )
        }
        self.sac_aff = {
            group['id']['tail']: [e for e in group['values']] for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Affinity_Score",
                groupby='tail',
                select='head,weight'
            )
        }

    def _enforce_committee_membership(self, logger: logging.Logger | None = None) -> None:
        """Filter SAC/AC keyed data down to active group members."""
        logger = logger or logging.getLogger(__name__)
        sac_members = set(getattr(self.sacs, 'members', []))
        ac_members = set(getattr(self.acs, 'members', []))
        allowed_ids = sac_members | ac_members

        def _filter_profiles(profiles, allowed):
            if profiles is None:
                return profiles
            return [profile for profile in profiles if getattr(profile, 'id', None) in allowed]

        def _filter_dict(data, allowed):
            if not isinstance(data, dict):
                return data
            return {key: value for key, value in data.items() if key in allowed}

        logger.debug(
            "Restricting committee data to %d SACs and %d ACs",
            len(sac_members),
            len(ac_members)
        )

        self.sacs_profiles = _filter_profiles(self.sacs_profiles, sac_members)
        self.acs_profiles = _filter_profiles(self.acs_profiles, ac_members)
        self.name_to_id = {
            name: pid for name, pid in self.name_to_id.items() if pid in allowed_ids
        }

        self.sac_reg = _filter_dict(self.sac_reg, sac_members)
        self.sac_to_tracks = _filter_dict(self.sac_to_tracks, sac_members)
        self.sac_priority_tracks = _filter_dict(self.sac_priority_tracks, sac_members)
        self.sac_cois = _filter_dict(self.sac_cois, sac_members)
        self.sac_aff = _filter_dict(self.sac_aff, sac_members)

        self.ac_reg = _filter_dict(self.ac_reg, ac_members)
        self.ac_to_tracks = _filter_dict(self.ac_to_tracks, ac_members)
        self.ac_loads = _filter_dict(self.ac_loads, ac_members)
        self.ac_cois = _filter_dict(self.ac_cois, ac_members)
        self.ac_cmp = _filter_dict(self.ac_cmp, ac_members)

    def _apply_sac_exclusions(self, logger: logging.Logger) -> None:
        """Remove excluded SACs from all MatchingData structures if provided."""
        if not self.exclude_sacs:
            return
        excl = set(self.exclude_sacs)
        # Filter SAC group members
        if hasattr(self, 'sacs') and getattr(self.sacs, 'members', None) is not None:
            self.sacs.members = [m for m in self.sacs.members if m not in excl]
        # Profiles
        if hasattr(self, 'sacs_profiles'):
            self.sacs_profiles = [p for p in self.sacs_profiles if p.id not in excl]
        # Registrations/maps
        if hasattr(self, 'sac_reg'):
            self.sac_reg = {k: v for k, v in self.sac_reg.items() if k not in excl}
        if hasattr(self, 'sac_to_tracks'):
            self.sac_to_tracks = {k: v for k, v in self.sac_to_tracks.items() if k not in excl}
        if hasattr(self, 'sac_priority_tracks'):
            self.sac_priority_tracks = {k: v for k, v in self.sac_priority_tracks.items() if k not in excl}
        # Edges/maps
        if hasattr(self, 'sac_cois'):
            self.sac_cois = {k: v for k, v in self.sac_cois.items() if k not in excl}
        if hasattr(self, 'sac_aff'):
            self.sac_aff = {k: v for k, v in self.sac_aff.items() if k not in excl}

    def _populate_matching_configs(self, logger: logging.Logger) -> None:
        """Fill matching configs."""
        logger.debug("Populating matching configs …")
        self.ac_matching_config = DEFAULT_AC_MATCHING_CONFIG
        for key, value in DEFAULT_AC_MATCHING_CONFIG.items():
            if isinstance(value['value'], str):
                self.ac_matching_config[key]['value'] = value['value'].replace(
                    'VENUE_ID', self.venue_id
                )
            elif isinstance(value['value'], dict):
                new_dict = {}
                for subkey, subvalue in value['value'].items():
                    new_key = subkey.replace('VENUE_ID', self.venue_id)
                    new_dict[new_key] = subvalue
                    #del self.ac_matching_config[key]['value'][subkey]
                self.ac_matching_config[key]['value'] = new_dict

        self.sac_matching_config = DEFAULT_SAC_MATCHING_CONFIG
        for key, value in DEFAULT_SAC_MATCHING_CONFIG.items():
            if isinstance(value['value'], str):
                self.sac_matching_config[key]['value'] = value['value'].replace(
                    'VENUE_ID', self.venue_id
                )
            elif isinstance(value['value'], dict):
                new_dict = {}
                for subkey, subvalue in value['value'].items():
                    new_key = subkey.replace('VENUE_ID', self.venue_id)
                    new_dict[new_key] = subvalue
                    #del self.sac_matching_config[key]['value'][subkey]
                self.sac_matching_config[key]['value'] = new_dict

    def dump_edges_and_notes(self, file_path):
        with open(file_path, 'w') as f:
            json.dump({
                'edges': self.client.get_edges(),
                'notes': self.client.get_notes()
            }, f)
        
class MatcherInterface:
    def __init__(self, client_v1, client_v2, venue_id, matcher_baseurl='http://localhost:5000'):
        """
        MatcherInterface handles matcher API calls.
        """
        self.client_v1 = client_v1
        self.client = client_v2
        self.venue_id = venue_id
        self.matcher_baseurl = matcher_baseurl

        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[ 500, 502, 503, 504 ], respect_retry_after_header=True))
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

    def __handle_response(self, response):
        try:
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if 'application/json' in response.headers.get('Content-Type', ''):
                error = response.json()
            elif response.text:
                error = {
                    'name': 'Error',
                    'message': response.text
                }
            else:
                error = {
                    'name': 'Error',
                    'message': response.reason
                }
            raise openreview.OpenReviewException(error)
        
    def _time_to_unix_millis(self):
        return int(time.time() * 1000)

    def post_configuration_note_edit(self, config, committee_name, title=None):
        run_content = deepcopy(config)
        if title is None:
            run_content['title']['value'] = f"run-{self._time_to_unix_millis()}"
        else:
            run_content['title']['value'] = title
        run_content['status']['value'] = 'Initialized'

        config_note_edit = self.client.post_note_edit(
            invitation=f"{self.venue_id}/{committee_name}/-/Assignment_Configuration",
            readers=[self.venue_id],
            writers=[self.venue_id],
            signatures=[self.venue_id],
            note=openreview.api.Note(
                content=run_content
            )
        )
        return config_note_edit
    
    def post_matcher(self, config_note_id):
        response = self.session.post(
            f"{self.matcher_baseurl}/match",
            json={"configNoteId": config_note_id},
            headers=self.client.headers,
        )
        response = self.__handle_response(response)
        return response.json()
    
    def get_matcher_status(self, config_note_id):
        config_note = self.client.get_note(config_note_id)
        return (
            config_note.content['status']['value'],
            config_note.content.get('error_message', {}).get('value', '')
        )
        
class SACACMatching:

    def __init__(
            self,
            client_v1,
            client_v2,
            request_form_id,
            matcher_baseurl='http://localhost:5000',
            cutoff=None,
            checkpoint=None
        ):
        self.client_v1 = client_v1
        self.client = client_v2

        if 'localhost' in [self.client_v1.baseurl, self.client.baseurl]:
            SUPPORT_GROUP = 'openreview.net/Support'
        else:
            SUPPORT_GROUP = 'OpenReview.net/Support'

        self.venue = openreview.helpers.get_conference(client_v1, request_form_id, SUPPORT_GROUP)
        self.venue_id = self.venue.id
        self.matching_data = MatchingData(
            client_v2,
            self.venue_id,
            exclude_sacs=set(checkpoint.get('exclude_sacs', [])) if checkpoint else None,
        )
        self.matcher = MatcherInterface(client_v1, client_v2, self.venue_id, matcher_baseurl)

        self.cutoff = cutoff
        self.checkpoint = checkpoint
        # Checkpoint is a dict of intermediate data to know the progress of the matching

        self.acs_to_sac = None
        self.ac_to_tracks = None
        self.sac_to_many_tracks = None

    # ---------------------------------------------------------------------- #
    # helper functions
    # ---------------------------------------------------------------------- #

    def load_checkpoint_from_file(self, file_path):
        with open(file_path, 'r') as f:
            self.checkpoint = json.load(f)

    def load_checkpoint_from_invitation(self, invitation):
        pass

    def save_checkpoint_to_file(self, file_path):
        with open(file_path, 'w') as f:
            json.dump(self.checkpoint, f)

    def update_track_edges(self, user_to_tracks, role_name):
        count = self.client.get_edges_count(
            invitation=f"{self.venue_id}/{role_name}/-/Research_Area"
        )
        print(f"Found {count} existing {role_name} Research_Area edges")
        if count > 0:
            delete_edges_with_polling(
                self.client,
                invitation=f"{self.venue_id}/{role_name}/-/Research_Area",
                soft_delete=False,
            )

        edge_readers = []
        if role_name == 'Senior_Area_Chairs':
            edge_readers = [
                self.venue_id,
            ]
        elif role_name == 'Area_Chairs':
            edge_readers = [
                self.venue_id,
                f"{self.venue_id}/Senior_Area_Chairs"
            ]

        edges = []
        for user_id, tracks in user_to_tracks.items():
            for track in tracks:
                for submission in self.matching_data.submissions_by_track[track]:
                    edges.append(
                        openreview.api.Edge(
                            invitation=f"{self.venue_id}/{role_name}/-/Research_Area",
                            head=submission.id,
                            tail=user_id,
                            weight=1,
                            label=track,
                            readers=edge_readers + [user_id],
                            writers=[self.venue_id],
                            signatures=[self.venue_id]
                        )
                    )
        openreview.tools.post_bulk_edges(self.client, edges)

    def submit_and_wait_ac_matching(self, title=None):
        config_note_edit = self.matcher.post_configuration_note_edit(
            self.matching_data.ac_matching_config, 
            'Area_Chairs',
            title
        )
        title = config_note_edit['note']['content']['title']['value']
        config_note_id = config_note_edit['note']['id']

        # Run the matcher
        response = self.matcher.post_matcher(config_note_id)

        # Wait for complete or error
        termination_states = [
            "Error",
            "No Solution",
            "Complete",
            "Cancelled"
        ]
        status = ''
        call_count = 0
        while status not in termination_states:
            if call_count == 1440: ## one day to wait the completion or trigger a timeout
                break
            time.sleep(60)
            status, error_message = self.matcher.get_matcher_status(config_note_id)
        if 'Error' in status:
            raise openreview.OpenReviewException(f"Error on id={title} , description: {error_message}")
        if call_count == 1440:
            raise openreview.OpenReviewException(f"Time out on id={title}")
        
        return title
    
    # ---------------------------------------------------------------------- #
    # workflow functions
    # ---------------------------------------------------------------------- #

    def create_priority_track_plan(self, ptl_cfg):
        papers_by_track = {t: len(self.matching_data.submissions_by_track.get(t, [])) for t in self.matching_data.submissions_by_track}
        sac_priority_tracks = getattr(self.matching_data, 'sac_priority_tracks', None) or self.matching_data.sac_to_tracks
        sac_ids = list(self.matching_data.sac_reg.keys())
        plan = compute_priority_track_load_plan(
            sac_ids,
            papers_by_track,
            sac_priority_tracks,
            self.matching_data.sac_to_tracks,
            small_track_min_papers=int(ptl_cfg.get('small_track_min_papers', 10)),
            small_track_percent_of_median=float(ptl_cfg.get('small_track_percent_of_median', 0.2)),
        )
        self.matching_data.priority_track_load_plan = plan
        return plan

    def map_sacs_to_single_track(self):
        track_counts = {
            track: len(self.matching_data.submissions_by_track[track])
            for track in arr_tracks
        }
        return multiple_sac_tracks_to_single_track(self.matching_data.sac_to_tracks, track_counts)

    def combine_sac_tracks(self, sac_to_single_track, threshold):
        track_counts = {
            track: len(self.matching_data.submissions_by_track[track])
            for track in arr_tracks
        }
        sac_to_many_tracks, sac_loads, track_graph = rebalance_sacs_across_tracks(
            sac_to_single_track,
            track_counts,
            self.matching_data.track_fallback,
            threshold
        )
        self.checkpoint['track_graph'] = track_graph
        print(f"track_graph: {json.dumps(track_graph, indent=4)}")
        return sac_to_many_tracks, sac_loads, track_graph
    
    def update_sac_track_edges(self, sac_to_tracks):
        self.update_track_edges(sac_to_tracks, 'Senior_Area_Chairs')

    def map_acs_to_tracks(self, matching_title):
        ac_to_tracks = {}
        prop_asms = {
            group['id']['tail']: group['values'] for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Area_Chairs/-/Proposed_Assignment",
                groupby='tail',
                label=matching_title
            )
        }
        for ac, edges in prop_asms.items():
            research_area_counts = Counter(self.matching_data.submission_to_track[edge['head']] for edge in edges)
            ac_to_tracks[ac] = [research_area_counts.most_common(1)[0][0]]
            #print(f"{ac} -> {ac_to_tracks[ac]}")
            #print(research_area_counts)

        valid_acs = set(getattr(self.matching_data.acs, 'members', []))
        filtered_ac_to_tracks = {
            ac_id: tracks for ac_id, tracks in ac_to_tracks.items() if ac_id in valid_acs
        }
        self.matching_data.ac_to_tracks = filtered_ac_to_tracks
        self.matching_data._enforce_committee_membership()
        
        return filtered_ac_to_tracks

    def update_ac_track_edges(self, ac_to_tracks):
        self.update_track_edges(ac_to_tracks, 'Area_Chairs')

    def get_ac_proposed_loads(self, matching_title):
        prop_asms = {
            group['id']['tail']: [openreview.api.Edge(e) for e in group['values']] for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Area_Chairs/-/Proposed_Assignment",
                groupby='tail',
                label=matching_title
            )
        }
        return {
            ac: len(edges) for ac, edges in prop_asms.items()
        }

    def map_acs_to_sacs(
        self,
        matching_title,
        sac_tracks,
        ac_tracks,
        track_graph,
        sac_max_loads: Mapping[str, int] | None = None,
    ):
        track_counts = {
            track: len(self.matching_data.submissions_by_track[track])
            for track in arr_tracks
        }
        sac_cois = {sac_id: [e['head'] for e in edges] for sac_id, edges in self.matching_data.sac_cois.items()}
        ac_asms = {
            group['id']['tail']: [e['head'] for e in group['values']] for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Area_Chairs/-/Proposed_Assignment",
                groupby='tail',
                label=matching_title
            )
        }
        sac_to_acs = assign_acs_to_sac(
            ac_tracks,
            sac_tracks,
            self.matching_data.sac_to_tracks,
            track_graph,
            track_counts,
            ac_asms,
            sac_cois,
            sac_max_loads,
        )
        return sac_to_acs
    
    def transfer_conflicts(self, sac_to_acs):
        sac_cois = {
            sac_id: [e['head'] for e in edges] for sac_id, edges in self.matching_data.sac_cois.items()
        }
        ac_cois = {
            ac_id: [e['head'] for e in edges] for ac_id, edges in self.matching_data.ac_cois.items()
        }
        new_conflicts = []
        for sac_id, acs in sac_to_acs.items():
            for ac_id in acs:
                if ac_id not in ac_cois:
                    print(f"no cois for {ac_id}")
                    continue
                for coi_to_add in sac_cois.get(sac_id, []):
                    if coi_to_add not in ac_cois[ac_id]:
                        new_conflicts.append(openreview.api.Edge(
                            invitation=f"{self.venue_id}/Area_Chairs/-/Conflict",
                            head=coi_to_add,
                            tail=ac_id,
                            weight=-1,
                            label='Conflict',
                            readers=[
                                self.venue_id,
                                f"{self.venue_id}/Senior_Area_Chairs",
                                ac_id
                            ],
                            writers=[self.venue.id],
                            signatures=[self.venue.id]
                        ))
        openreview.tools.post_bulk_edges(self.client, new_conflicts)

    def infer_sac_assignments(self, ac_matching_title, sac_to_acs, sac_title, create_note):
        if create_note:
            config_note_edit = self.matcher.post_configuration_note_edit(
                self.matching_data.sac_matching_config, 
                'Senior_Area_Chairs',
                sac_title
            )
            self.client.post_note_edit(
                invitation=self.venue.get_meta_invitation_id(),
                readers=[self.venue_id],
                writers=[self.venue_id],
                signatures=[self.venue_id],
                note=openreview.api.Note(
                    id=config_note_edit['note']['id'],
                    content={
                        'status': {
                            'value': 'Complete'
                        }
                    }
                )
            )
        ac_asms = {
            group['id']['tail']: [e['head'] for e in group['values']] for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Area_Chairs/-/Proposed_Assignment",
                groupby='tail',
                label=ac_matching_title
            )
        }

        sac_paper_asms = []
        for sac_id, acs in sac_to_acs.items():
            for ac_id in acs:
                if ac_id in ac_asms:
                    for ac_paper in ac_asms[ac_id]:
                        sac_paper_asms.append(openreview.api.Edge(
                            invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Proposed_Assignment",
                            readers=[
                                self.venue_id,
                                sac_id
                            ],
                            writers=[self.venue.id],
                            signatures=[self.venue.id],
                            head=ac_paper,
                            tail=sac_id,
                            weight=1,
                            label=sac_title
                        ))
        delete_edges_with_polling(
            self.client,
            invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Proposed_Assignment",
            label=sac_title,
            soft_delete=False,
        )
        openreview.tools.post_bulk_edges(self.client, sac_paper_asms)

    def post_sac_aggregate_scores(self, sac_title, top_n):
        time.sleep(10)

        # Post aggregate scores
        edges_to_post = []
        asms_to_post = []
        affinity_scores = self.matching_data.sac_aff ## by tail
        affinity_scores_dict = {
            sac_id: {
                edge['head']: edge['weight'] for edge in edges
            } for sac_id, edges in affinity_scores.items()
        }
        track_edges = {
            group['id']['tail']: [e['head'] for e in group['values']] for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Research_Area",
                groupby='tail',
                select='head'
            )
        }
        proposed_assignments = {
            group['id']['tail']: [e['head'] for e in group['values']] for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Proposed_Assignment",
                groupby='tail',
                label=sac_title
            )
        }
        submission_id_to_number = {
            submission.id: submission.number for submission in self.matching_data.all_submissions
        }
        for sac, edges in affinity_scores.items():
            asms = proposed_assignments.get(sac, [])
            # edges is a list of dicts with head and weight keys
            # sort edges in descending order and keep top 100
            edges.sort(key=lambda x: x['weight'], reverse=True)
            top_n_edges = edges[:top_n]
            track_heads = track_edges[sac]
            for edge in top_n_edges:
                score = edge['weight']
                if edge['head'] in track_heads:
                    score += 1
                edges_to_post.append(
                    openreview.api.Edge(
                        head=edge['head'],
                        tail=sac,
                        weight=score,
                        label=sac_title,
                        invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Aggregate_Score",
                        readers=[
                            self.venue_id,
                            sac
                        ],
                        writers=[self.venue_id],
                        signatures=[self.venue_id],
                    )
                )
        
        for sac, asms in proposed_assignments.items():
            track_heads = track_edges[sac]
            for asm in asms:
                submission_number = submission_id_to_number[asm]
                score = affinity_scores_dict.get(sac, {}).get(asm, 0)
                if asm in track_heads:
                    score += 1
                asms_to_post.append(
                    openreview.api.Edge(
                        head=asm,
                        tail=sac,
                        weight=score,
                        label=sac_title,
                        invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Proposed_Assignment",
                        readers=[
                            self.venue_id,
                            sac
                        ],
                        nonreaders=[
                            f"{self.venue_id}/Submission{submission_number}/Authors"
                        ],  
                        writers=[self.venue_id],
                        signatures=[self.venue_id],
                    )
                )
            
        delete_edges_with_polling(
            self.client,
            invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Aggregate_Score",
            label=sac_title,
        )
        openreview.tools.post_bulk_edges(self.client, edges_to_post)

        delete_edges_with_polling(
            self.client,
            invitation=f"{self.venue_id}/Senior_Area_Chairs/-/Proposed_Assignment",
            label=sac_title,
        )
        openreview.tools.post_bulk_edges(self.client, asms_to_post)

    # ---------------------------------------------------------------------- #
    # workflow functions
    # ---------------------------------------------------------------------- #

    def reset_ac_cois(self):
        self.venue.setup_committee_matching(
            committee_id=self.venue.get_area_chairs_id(),
            compute_affinity_scores=False,
            compute_conflicts=True,
            compute_conflicts_n_years=None,
            alternate_matching_group=None,
            submission_track=None
        )
        self.matching_data.ac_cois = {
            group['id']['tail']: [e for e in group['values']] for group in self.client.get_grouped_edges(
                invitation=f"{self.venue_id}/Area_Chairs/-/Conflict",
                groupby='tail'
            )
        }
        self.matching_data._enforce_committee_membership()

    def run_matching(self, threshold=1, sac_title=None, ac_title=None):

        # Search checkpoint to determine workflow
        run_matching_one, run_matching_two, run_matching_three, post_sac_assignment_note = True, True, True, True
        title_one, title_two, title_three = None, None, None
        skip_sac_setup = self.checkpoint.get('skip_sac_update', False)
        skip_ac_track_update = self.checkpoint.get('skip_ac_update', False)
        skip_transfer_conflicts = self.checkpoint.get('skip_transfer_conflicts', False)
        skip_sac_assignments = self.checkpoint.get('skip_sac_assignments', False)
        skip_sac_aggregate_scores = self.checkpoint.get('skip_sac_aggregate_scores', False)
        config_note_one = openreview.tools.get_note(self.client, self.checkpoint.get('matching_one', 'N/A'))
        config_note_two = openreview.tools.get_note(self.client, self.checkpoint.get('matching_two', 'N/A'))
        config_note_three = openreview.tools.get_note(self.client, self.checkpoint.get('matching_three', 'N/A'))
        config_note_sac = openreview.tools.get_note(self.client, self.checkpoint.get('sac_matching', 'N/A'))
        top_n = self.checkpoint.get('top_n', 100)
        checkpoint_sac_max_loads = self.checkpoint.get('sac_max_loads')
        ptl_cfg = self.checkpoint.get('priority_track_loads', {})
        priority_tracks_enabled = ptl_cfg.get('enabled', False)

        if config_note_one:
            run_matching_one = config_note_one.content['status']['value'] != 'Complete'
            title_one = config_note_one.content['title']['value']
        if config_note_two:
            run_matching_two = config_note_two.content['status']['value'] != 'Complete'
            title_two = config_note_two.content['title']['value']
        if config_note_three:
            run_matching_three = config_note_three.content['status']['value'] != 'Complete'
            title_three = config_note_three.content['title']['value']
        if config_note_sac:
            post_sac_assignment_note = config_note_sac.content['status']['value'] != 'Complete'

        if sac_title is None:
            sac_title = f"sac-matching"
        if ac_title is None:
            ac_title = f"ac-matching"

        # Reset any data depending on checkpoint
        reset_sac_tracks = self.checkpoint.get('reset_sac_tracks', False)
        reset_ac_tracks = self.checkpoint.get('reset_ac_tracks', False)
        if reset_sac_tracks:
            self.update_sac_track_edges(self.matching_data.sac_to_tracks)
        if reset_ac_tracks:
            self.update_ac_track_edges(self.matching_data.ac_to_tracks)

        # Main workflow
        if priority_tracks_enabled:
            plan = self.create_priority_track_load_plan(ptl_cfg)
            # Derive SAC→tracks including volunteers for downstream edge updates
            sac_to_many_tracks = merge_sac_tracks_with_volunteers(
                self.matching_data.sac_to_tracks,
                plan.volunteered_tracks,
            )
            track_graph = {}
            self.sac_to_many_tracks = sac_to_many_tracks
        else:
            sac_to_single_track = self.map_sacs_to_single_track()
            sac_to_many_tracks, _, track_graph = self.combine_sac_tracks(sac_to_single_track, threshold)
            self.sac_to_many_tracks = sac_to_many_tracks

        # if priority tracks, areas already updated
        if not skip_sac_setup and not priority_tracks_enabled:
            self.update_sac_track_edges(sac_to_many_tracks)
        if run_matching_one:
            title_one = self.submit_and_wait_ac_matching() # naive
        ac_to_tracks = self.map_acs_to_tracks(title_one)
        self.ac_to_tracks = ac_to_tracks
        if not skip_ac_track_update:
            self.update_ac_track_edges(ac_to_tracks)
        if run_matching_two:
            title_two = self.submit_and_wait_ac_matching() # track-constrained
        sac_to_acs = self.map_acs_to_sacs(title_two, sac_to_many_tracks, ac_to_tracks, track_graph, sac_max_loads=checkpoint_sac_max_loads)
        self.acs_to_sac = sac_to_acs
        if not skip_transfer_conflicts:
            self.transfer_conflicts(sac_to_acs)
        if run_matching_three:
            title_three = self.submit_and_wait_ac_matching(ac_title) # SAC-constrained
        if not skip_sac_assignments:
            self.infer_sac_assignments(title_three, sac_to_acs, sac_title, post_sac_assignment_note)
        if not skip_sac_aggregate_scores:
            self.post_sac_aggregate_scores(sac_title, top_n)
        # self.validate_matching()

'''
Example checkpoint:
{
    'skip_sac_setup': False,
    'matching_one': 'N/A',
    'matching_two': 'N/A',
    'matching_three': 'N/A',
    'reset_sac_tracks': False,
    'reset_ac_tracks': False,
}
'''

# 1. If SACs have multiple tracks, map all SACs to a single track (compare number of SACs, tracks per SAC, and submissions per track)
# 1a. Skip if SACs only have 1 track
# 1b. Compute quota for SACs - PARAMETERIZE cutoff, balance within track, if variance of SACs exceeds cutoff, use global balancing
# 1c. Question: if one track has substantially less submissions than others, who should they share with?
# 1c1. Maybe this can look like fractional weight research area edges?
# 2. Compute naive ACs-paper matching (1st)
# 3. Use voting to assign track to ACs
# 3a. Check number of submissions assigned by track to the ACs
# 4. Compute track-constrained ACs-paper matching (2nd)
# 5. Compute mapping of ACs to SACs that minimizes conflicts per track
# 6. Transfer conflicts of SACs to ACS
# 7. Compute final track-constrained SAC-constrained ACs-paper matching (3rd)
# 8. Infer final SAC-paper assignments
# 9. Sanity check and cleanup (1st and 2nd matching data, notes)
