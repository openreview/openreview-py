import openreview, requests, time

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Dict, List, Optional, Set, Tuple, Union
from copy import deepcopy

from decorators import require_confirmation
from edge_utils import EdgeUtils
from profile_utils import ProfileUtils
from note_utils import NoteUtils
from constants import (
    DEFAULT_REVIEWER_MATCHING_CONFIG,
    DEFAULT_AC_MATCHING_CONFIG,
    DEFAULT_SAC_MATCHING_CONFIG,
)

class MatcherInterface:
    def __init__(self, client, venue_id, matcher_baseurl='http://localhost:5000'):
        """
        MatcherInterface handles matcher API calls.
        """
        self.client = client
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

    def _load_default_config(self, committee_name):
        """Loads the default configuration for a given committee name.
        Args:
            committee_name: The name of the committee to load the default configuration for.
        Returns:
            The default configuration for the given committee name.
        """
        config = None
        if committee_name == 'Reviewers' or committee_name.endswith('/Reviewers'):
            config = deepcopy(DEFAULT_REVIEWER_MATCHING_CONFIG)
        elif committee_name == 'Area_Chairs' or committee_name.endswith('/Area_Chairs'):
            config = deepcopy(DEFAULT_AC_MATCHING_CONFIG)
        elif committee_name == 'Senior_Area_Chairs' or committee_name.endswith('/Senior_Area_Chairs'):
            config = deepcopy(DEFAULT_SAC_MATCHING_CONFIG)
        else:
            raise ValueError(f"Invalid committee name: {committee_name}")

        for key, value in config.items():
            if isinstance(value['value'], str):
                config[key]['value'] = value['value'].replace(
                    'VENUE_ID', self.venue_id
                )
            elif isinstance(value['value'], dict):
                new_dict = {}
                for subkey, subvalue in value['value'].items():
                    new_key = subkey.replace('VENUE_ID', self.venue_id)
                    new_dict[new_key] = subvalue
                config[key]['value'] = new_dict

        return config

    @require_confirmation
    def post_configuration_note_edit(
        self,
        committee_name: str,
        title: Optional[str] = None,
        dry_run: bool = False
    ):
        """Posts a configuration note edit for a given committee name.

        Useful for posting edges to a new note or for running a new matching

        Args:
            committee_name: The name of the committee to post the configuration note edit for.
            title: The title of the configuration note edit.
            dry_run: If True, skip confirmation prompt and return without posting the configuration note edit.
        Returns:
            The configuration note edit.
        """
        run_content = self._load_default_config(committee_name)
        if title is None:
            run_content['title']['value'] = f"run-{self._time_to_unix_millis()}"
        else:
            run_content['title']['value'] = title
        run_content['status']['value'] = 'Initialized'

        if self.venue_id in committee_name:
            invitation = f"{self.venue_id}/{committee_name}/-/Assignment_Configuration"
        else:
            invitation = f"{committee_name}/-/Assignment_Configuration"

        if not dry_run:
            config_note_edit = self.client.post_note_edit(
                invitation=invitation,
                readers=[self.venue_id],
                writers=[self.venue_id],
                signatures=[self.venue_id],
                note=openreview.api.Note(
                    content=run_content
                )
            )
            return config_note_edit
        else:
            return {
                'note': {
                    'id': f"{self.venue_id}/{committee_name}/-/Assignment_Configuration",
                    'content': run_content
                }
            }
    
    @require_confirmation
    def post_matcher(self, config_note_id, dry_run: bool = False):
        """HTTP Wrapper for posting a matcher request to the matcher API.
        Args:
            config_note_id: The ID of the configuration note to post the matcher request for.
            dry_run: If True, skip confirmation prompt and return without posting the matcher request.
        Returns:
            The matcher request response.
        """
        if not dry_run:
            response = self.session.post(
                f"{self.matcher_baseurl}/match",
                json={"configNoteId": config_note_id},
                headers=self.client.headers,
            )
            response = self.__handle_response(response)
            return response.json()
        else:
            return {}
    
    def get_matcher_status(self, config_note_id):
        """Gets the status of a matcher request from the configuration note."""
        config_note = self.client.get_note(config_note_id)
        return (
            config_note.content['status']['value'],
            config_note.content.get('error_message', {}).get('value', '')
        )

class AssignmentsBuilder(object):
    def __init__(
        self,
        arr_matcher
    ):
        self.client = arr_matcher.client
        self.venue = arr_matcher.venue
        self.matcher = MatcherInterface(self.client, self.venue.id, matcher_baseurl=self.client.baseurl)

    def run_automatic_assignment(
        self,
        group_id: str,
        dry_run: bool = False
    ):
        """Runs the automatic assignment process.

        Args:
            group_id: The ID of the group to run the automatic assignment process on.
            dry_run: If True, skip confirmation prompt and return without running the automatic assignment process.
        """
        config_note_edit = self.matcher.post_configuration_note_edit(
            committee_name=group_id,
            dry_run=dry_run
        )
        config_note_id = config_note_edit['note']['id']
        title = config_note_edit['note']['content']['title']['value']
        response = self.matcher.post_matcher(config_note_id, dry_run=dry_run)
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
            call_count += 1
            status, error_message = self.matcher.get_matcher_status(config_note_id)
        if 'Error' in status:
            raise openreview.OpenReviewException(f"Error on id={title} , description: {error_message}")
        if call_count == 1440:
            raise openreview.OpenReviewException(f"Time out on id={title}")
        
        return self.client.get_note(config_note_id)
    
    @require_confirmation
    def compute_conflicts(
        self,
        group_id: str,
        num_years: int,
        dry_run: bool = False
    ):
        """Computes conflicts for a given group by calling setup_committee_matching.

        The conflicts look at the last num_years of profile history between authors and the group members

        Args:
            group_id: The ID of the group to compute conflicts for.
            num_years: The number of years to compute conflicts for.
            dry_run: If True, skip confirmation prompt and return without computing the conflicts.
        """
        if not dry_run:
            return self.venue.setup_committee_matching(
                group_id,
                None,
                'Default',
                num_years,
                alternate_matching_group=None,
                submission_track=None
            )
        else:
            return {}

    @require_confirmation
    def compute_affinity_scores(
        self,
        group_id: str,
        dry_run: bool = False
    ):
        """Computes affinity scores for a given group by calling setup_committee_matching.
        Args:   
            group_id: The ID of the group to compute affinity scores for.
            dry_run: If True, skip confirmation prompt and return without computing the affinity scores.
        """
        if not dry_run:
            return self.venue.setup_committee_matching(
                group_id,
                'specter2+scincl',
                None,
                None,
                alternate_matching_group=None,
                submission_track=None
            )
        else:
            return {}

    def sync_research_areas(
        self,
        group_id: str,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Syncs the research areas for a given group by looking at the registration notes
        Args:
            group_id: The ID of the group to sync the research areas for.
            dry_run: If True, skip confirmation prompt and return without syncing the research areas.
        """

        # Load profile data
        profile_id_to_research_areas = {}
        members = self.client.get_group(group_id)
        profiles = ProfileUtils.get_valid_profiles(self.client, members.members)

        # Load registration forms to build profile_id_to_research_areas map
        registration_forms = self.client.get_all_notes(
            invitation=f"{group_id}/-/Registration"
        )
        name_to_note = NoteUtils.map_profile_names_to_note(
            self.client,
            registration_forms
        )
        for profile in profiles:
            if profile.id not in name_to_note:
                continue

            research_areas = name_to_note[profile.id].content['research_area']['value']
            profile_id_to_research_areas[profile.id] = research_areas

        return self.post_research_areas(
            group_id=group_id,
            profile_id_to_research_areas=profile_id_to_research_areas,
            dry_run=dry_run
        )

    @require_confirmation
    def post_research_areas(
        self,
        group_id: str,
        profile_id_to_research_areas: Dict[str, List[str]],
        dry_run: bool = False
    ):
        """Posts research area edges between the profiles and the submissions corresponding to the research areas.
        Args:
            group_id: The ID of the group to post the research area edges for.
            profile_id_to_research_areas: A dictionary mapping profile IDs to research areas.
            dry_run: If True, skip confirmation prompt and return without posting the research area edges.
        """

        # Fetch submission data
        edges_to_post = []
        submissions = self.client.get_all_notes(
            invitation=f"{self.venue.id}/-/Submission"
        )
        submission_id_to_number = {
            submission.id: submission.number for submission in submissions
        }

        # Build research area submission map
        research_area_to_submissions = {}
        for submission in submissions:
            for research_area in submission.content['research_area']['value']:
                if research_area not in research_area_to_submissions:
                    research_area_to_submissions[research_area] = []
                research_area_to_submissions[research_area].append(submission.id)

        # Validate research areas
        all_profile_research_areas = set()
        for research_areas in profile_id_to_research_areas.values():
            all_profile_research_areas.update(research_areas)
        for research_area in all_profile_research_areas:
            if research_area not in research_area_to_submissions:
                raise ValueError(f"Research area {research_area} not found in research_area_to_submissions")

        for profile_id, research_areas in profile_id_to_research_areas.items():
            for research_area in research_areas:
                for submission_id in research_area_to_submissions[research_area]:
                    permissions = EdgeUtils.build_readers_writers_signatures_nonreaders(
                        venue=self.venue,
                        invitation=f"{group_id}/-/Research_Area",
                        tail=profile_id,
                        paper_number=submission_id_to_number[submission_id]
                    )
                    edges_to_post.append(
                        openreview.api.Edge(
                            head=submission_id,
                            tail=profile_id,
                            label=research_area,
                            **permissions
                        )
                    )

        post_return = EdgeUtils.post_bulk_edges(
            client=self.client,
            edges=edges_to_post,
            dry_run=dry_run
        )
        return {
            'research_areas_posted': post_return['edges_posted'],
        }

    def sync_max_loads(
        self,
        group_id: str,
        dry_run: bool = False
    ):
        """Syncs the max loads for a given group to their responses to the maximum load form
        This is useful to ensure that the matcher max loads are consistent with the responses to the maximum load form.
        Args:
            group_id: The ID of the group to sync the max loads for.
            dry_run: If True, skip confirmation prompt and return without syncing the max loads.
        """

        # Load profile data
        profile_id_to_max_load = {}
        members = self.client.get_group(group_id)
        profiles = ProfileUtils.get_valid_profiles(self.client, members.members)

        # Load max load forms to build profile_id_to_max_load map
        max_load_forms = self.client.get_all_notes(
            invitation=f"{group_id}/-/Max_Load_And_Unavailability_Request"
        )
        name_to_note = NoteUtils.map_profile_names_to_note(
            self.client,
            max_load_forms
        )
        for profile in profiles:
            if profile.id not in name_to_note:
                continue

            max_load = int(name_to_note[profile.id].content['maximum_load_this_cycle']['value'])
            profile_id_to_max_load[profile.id] = max_load

        return self.post_max_loads(
            group_id=group_id,
            profile_id_to_loads=profile_id_to_max_load,
            dry_run=dry_run
        )

    @require_confirmation
    def post_max_loads(
        self,
        group_id: str,
        profile_id_to_loads: Dict[str, int],
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Posts custom max papers edges for profiles based on the given profile_id_to_loads map.
        Args:
            group_id: The ID of the group to post the max loads for.
            profile_id_to_loads: A dictionary mapping profile IDs to loads.
            dry_run: If True, skip confirmation prompt and return without posting the max loads.

        Returns:
            A dictionary containing the number of max loads posted.
            {
                'max_loads_posted': number_of_max_loads_posted
            }
        """

        edges_to_post = []
        for profile_id, load in profile_id_to_loads.items():
            permissions = EdgeUtils.build_readers_writers_signatures_nonreaders(
                venue=self.venue,
                invitation=f"{group_id}/-/Custom_Max_Papers",
                tail=profile_id
            )
            edges_to_post.append(openreview.api.Edge(
                head=profile_id,
                tail=profile_id,
                weight=load,
                **permissions
            ))

        post_return = EdgeUtils.post_bulk_edges(
            client=self.client,
            edges=edges_to_post,
            dry_run=dry_run
        )
        return {
            'loads_posted': post_return['edges_posted'],
        }