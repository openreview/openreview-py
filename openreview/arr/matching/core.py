import openreview, datetime
from typing import Dict, List, Optional
from assignments import AssignmentsBuilder
from decorators import require_confirmation
from sanity import SanityChecker
from registration import RegistrationBuilder

from profile_utils import ProfileUtils
from note_utils import NoteUtils

from openreview.arr.management.setup_reviewer_matching import process as setup_reviewer_matching
from openreview.arr.management.setup_ae_matching import process as setup_ac_matching
from openreview.arr.management.setup_sae_matching import process as setup_sac_matching

from constants import (
    PROFILE_ID_FIELD,
    DEFAULT_REGISTRATION_CONTENT,
    REGISTRATION_FORM_MAPPING,
    LICENSE_FORM_MAPPING,
    EMERGENCY_FORM_MAPPING
)

class ARRMatcher(object):
    def __init__(
            self,
            client: openreview.api.OpenReviewClient,
            request_form_id: str
    ):
        client_v1 = openreview.Client(baseurl='https://api.openreview.net', token=client.token)
        self.client = client
        self.venue = openreview.helpers.get_conference(
            client_v1,
            request_form_id
        )
        print(f"Loaded venue: {self.venue.id}")

        self.assignments_builder = AssignmentsBuilder(self)
        self.sanity_checker = SanityChecker(self)
        self.registration_builder = RegistrationBuilder(self)

    #region ====== Workflow functions ======

    # -- Pre-matching --

    def load_sacs_into_group(
        self,
        sac_tilde_ids: List[str],
        sac_to_priority_track: Dict[str, str],
        sac_to_all_tracks: Dict[str, List[str]],
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Loads SACs from variables into the SAC group, posting registration notes if they are missing.
        
        This method validates that all provided SAC profile IDs exist, validates that the specified
        tracks are valid, and ensures registration notes are posted/updated for each SAC.
        If any SAC does not have a profile, an error is raised.

        NOTE: The priority track should also be in the all tracks list. It will be added if not.
        
        Args:
            sac_tilde_ids: List of SAC profile IDs to load into the SAC group
            sac_to_priority_track: Dictionary mapping SAC profile ID to their priority track
            sac_to_all_tracks: Dictionary mapping SAC profile ID to list of all tracks they are assigned to
            dry_run: If True, skip confirmation prompt and return without making changes
        
        Returns:
            Dictionary containing statistics about the operation:
            - registration_notes_posted: Number of registration notes that were created
            - registration_notes_existing: Number of registration notes that already existed but edited
        
        Raises:
            ValueError: If any SAC profile ID does not have a corresponding profile
            ValueError: If any track name in the mappings is not valid for the venue
        """
        # Load profile data
        profiles: List[openreview.Profile] = ProfileUtils.get_valid_profiles(self.client, sac_tilde_ids)
        all_names: List[str] = ProfileUtils.get_all_profile_names(profiles)

        # Reset SAC group
        sac_profile_ids = [profile.id for profile in profiles]
        reset_group_members_result = ProfileUtils.reset_group_members(
            client=self.client,
            group_id=self.venue.get_senior_area_chairs_id(),
            target_members=sac_profile_ids,
            dry_run=dry_run
        )
        print(f"Reset SAC group members: {reset_group_members_result}")

        # Validate tracks
        for tracks in sac_to_all_tracks.values():
            self.sanity_checker.check_valid_tracks(tracks)
        for priority_track in sac_to_priority_track.values():
            self.sanity_checker.check_valid_tracks([priority_track])
        
        # Clear registration notes
        clear_registration_notes_result = self.registration_builder.clear_registration_notes(
            invitation=f'{self.venue.get_senior_area_chairs_id()}/-/Registration',
            valid_signatures=all_names,
            dry_run=dry_run
        )
        print(f"Clear registration notes: {clear_registration_notes_result}")

        # Build subset of content for research areas
        sac_to_raw_content: Dict[str, Dict] = {}
        for profile_id in sac_tilde_ids:
            # Validate priority track is in all tracks
            # If no tracks, set to priority track
            priority_track = sac_to_priority_track[profile_id]
            if priority_track not in sac_to_all_tracks[profile_id]:
                sac_to_all_tracks[profile_id].append(priority_track)
            if len(sac_to_all_tracks[profile_id]) == 0:
                sac_to_all_tracks[profile_id] = [priority_track]

            sac_to_raw_content[profile_id] = {
                'priority_research_area': {
                    'value': sac_to_priority_track[profile_id]
                },
                'research_area': {
                    'value': sac_to_all_tracks[profile_id]
                }
            }

        # Post registration notes
        posted_data = self.registration_builder.post_generic_registration_notes(
            invitation=f'{self.venue.get_senior_area_chairs_id()}/-/Registration',
            profiles=profiles,
            profile_ids_to_raw_content=sac_to_raw_content,
            dry_run=dry_run
        )
        print(f"Post registration notes: {posted_data}")

        return posted_data

    def migrate_authors_to_reviewers(
        self,
        author_tilde_ids: List[str],
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Migrates authors to reviewers by copying their forms to the reviewers group and reviewer forms.

        Authors must have a research area provided or they will be skipped, this field is required for registration.
        This process will fail if any provided author does not have a profile.
        This process will fail if default_load is not a positive integer.

        Args:
            author_tilde_ids: List of author profile IDs to migrate to the reviewers group
            default_load: Default load for the reviewers group
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation
        """
        return self.registration_builder.migrate_authors_to_role(
            author_tilde_ids=author_tilde_ids,
            target_group_id=self.venue.get_reviewers_id(),
            default_load=default_load,
            dry_run=dry_run
        )
    def migrate_authors_to_acs(
        self,
        author_tilde_ids: List[str],
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Migrates authors to area chairs by copying their responses to AC forms.

        Authors must have a research area provided or they will be skipped, this field is required for registration.
        This process will fail if any provided author does not have a profile.
        This process will fail if default_load is not a positive integer.

        Args:
            author_tilde_ids: List of author profile IDs to migrate to the area chairs group
            default_load: Default load for the area chairs group
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation
        """
        return self.registration_builder.migrate_authors_to_role(
            author_tilde_ids=author_tilde_ids,
            target_group_id=self.venue.get_area_chairs_id(),
            default_load=default_load,
            dry_run=dry_run
        )

    def shift_reviewers_to_acs(
        self,
        reviewer_tilde_ids: List[str],
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Shifts reviewers to area chairs by copying their responses to AC forms.

        This process will fail if any provided reviewer does not have a profile.

        Args:
            reviewer_tilde_ids: List of reviewer profile IDs to shift to the area chairs group
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation
        """
        return self.registration_builder.shift_roles(
            tilde_ids=reviewer_tilde_ids,
            source_group_id=self.venue.get_reviewers_id(),
            target_group_id=self.venue.get_area_chairs_id(),
            default_load=default_load,
            dry_run=dry_run
        )
    def shift_acs_to_reviewers(
        self,
        ac_tilde_ids: List[str],
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Shifts area chairs to reviewers by copying their responses to reviewer forms.

        This process will fail if any provided area chair does not have a profile.

        Args:
            ac_tilde_ids: List of area chair profile IDs to shift to the reviewers group
            default_load: Default load for the reviewers group
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation
        """
        return self.registration_builder.shift_roles(
            tilde_ids=ac_tilde_ids,
            source_group_id=self.venue.get_area_chairs_id(),
            target_group_id=self.venue.get_reviewers_id(),
            default_load=default_load,
            dry_run=dry_run
        )

    def make_reviewers_available(
        self,
        reviewer_tilde_ids: List[str],
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Makes reviewers available by posting a load note.

        Note: This will not change the availability of already available reviewers.

        Args:
            reviewer_tilde_ids: List of reviewer tilde IDs to make available.
            default_load: The default load for the reviewers group.
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation
        """
        return self.registration_builder.make_users_available(
            tilde_ids=reviewer_tilde_ids,
            group_id=self.venue.get_reviewers_id(),
            default_load=default_load,
            dry_run=dry_run
        )
    def make_acs_available(
        self,
        ac_tilde_ids: List[str],
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Makes area chairs available by posting a load note.

        Note: This will not change the availability of already available area chairs.

        Args:
            ac_tilde_ids: List of area chair tilde IDs to make available.
            default_load: The default load for the area chairs group.
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation
        """
        return self.registration_builder.make_users_available(
            tilde_ids=ac_tilde_ids,
            group_id=self.venue.get_area_chairs_id(),
            default_load=default_load,
            dry_run=dry_run
        )

    def check_reviewer_ac_overlap(self):
        """Checks if there is any overlap between the reviewers and area chairs groups.

        Returns:
            Dictionary containing statistics about the overlap
            - members_in_overlap: Number of members that are in both groups
            - members_not_in_overlap: Number of members that are not in either group
            - members_not_in_first_group: Number of members that are not in the first group
            - members_not_in_second_group: Number of members that are not in the second group
        """
        return self.sanity_checker.check_role_overlap(
            first_group_id=self.venue.get_reviewers_id(),
            second_group_id=self.venue.get_area_chairs_id()
        )

    def check_ac_sac_overlap(self):
        """Checks if there is any overlap between the area chairs and senior area chairs groups.

        Returns:
            Dictionary containing statistics about the overlap
            - members_in_overlap: Number of members that are in both groups
            - members_not_in_overlap: Number of members that are not in either group
            - members_not_in_first_group: Number of members that are not in the first group
            - members_not_in_second_group: Number of members that are not in the second group
        """
        return self.sanity_checker.check_role_overlap(
            first_group_id=self.venue.get_area_chairs_id(),
            second_group_id=self.venue.get_senior_area_chairs_id()
        )

    def check_sac_reviewer_overlap(self):
        """Checks if there is any overlap between the senior area chairs and reviewers groups.

        Returns:
            Dictionary containing statistics about the overlap
            - members_in_overlap: Number of members that are in both groups
            - members_not_in_overlap: Number of members that are not in either group
            - members_not_in_first_group: Number of members that are not in the first group
            - members_not_in_second_group: Number of members that are not in the second group
        """
        return self.sanity_checker.check_role_overlap(
            first_group_id=self.venue.get_senior_area_chairs_id(),
            second_group_id=self.venue.get_reviewers_id()
        )

    def setup_reviewer_matching_data(self):
        """
        Sets up reviewer matching data.

        Specifically, this function handles:

        1) Creating the submitted reviewers groups early
        2) Resetting the custom max papers edges to the values in the maximmum load notes
        3) Updating the affinity scores for resubmissions
            - 3 for requesting the same reviewer, 0 for requesting a different reviewer
        4) Posting the research area edges (reviewer -> paper with a matching track)
        5) Posting status edges to indicate reassigned or requested
        6) Posting seniority edges
        """
        return setup_reviewer_matching(
            client=self.client,
            invitation=f'{self.venue.id}/-/Setup_Reviewer_Matching'
        )

    def setup_ac_matching_data(self):
        """
        Sets up area chair matching data.

        Specifically, this function handles:

        1) Resetting the custom max papers edges to the values in the maximmum load notes
        2) Updating the affinity scores for resubmissions
            - 3 for requesting the same area chair, 0 for requesting a different area chair
        3) Posting the research area edges (area chair -> paper with a matching track)
        4) Posting status edges to indicate reassigned or requested
        """
        return setup_ac_matching(
            client=self.client,
            invitation=f'{self.venue.id}/-/Setup_AE_Matching'
        )

    def setup_sac_matching_data(self):
        """
        Sets up senior area chair matching data.

        Specifically, this function handles:

        1) Resetting the custom max papers edges assume equal loads per track
        3) Posting the research area edges (senior area chair -> paper with a matching track)
        """
        return setup_sac_matching(
            client=self.client,
            invitation=f'{self.venue.id}/-/Setup_SAE_Matching'
        )

    # -- Matching Stages --

    def run_ac_matching(
        self, 
        num_years: int,
        dry_run: bool = False
    ):

        # TODO: Decorator should display already posted data and check for missing data
        self.compute_ac_affinity_scores(dry_run=dry_run)
        self.compute_ac_conflicts(num_years=num_years, dry_run=dry_run)
        self.sync_ac_loads(dry_run=dry_run)
        self.sync_ac_tracks(dry_run=dry_run)
        return self.assignments_builder.run_automatic_assignment(
            group_id=self.venue.get_area_chairs_id(),
            dry_run=dry_run
        )

    def run_reviewer_matching(
        self,
        num_years: int,
        dry_run: bool = False
    ):

        self.compute_reviewer_affinity_scores(dry_run=dry_run)
        self.compute_reviewer_conflicts(num_years=num_years, dry_run=dry_run)
        self.sync_reviewer_loads(dry_run=dry_run)
        self.sync_reviewer_tracks(dry_run=dry_run)
        return self.assignments_builder.run_automatic_assignment(
            group_id=self.venue.get_reviewers_id(),
            dry_run=dry_run
        )

    def run_sac_ac_matching(self):
        pass

    # -- Post-matching --

    def run_sanity_checks(
        self,
        sac_assignment_title: Optional[str] = None,
        ac_assignment_title: Optional[str] = None,
        reviewer_assignment_title: Optional[str] = None
    ):
        return self.sanity_checker.run_sanity_checks(
            sac_assignment_title=sac_assignment_title,
            ac_assignment_title=ac_assignment_title,
            reviewer_assignment_title=reviewer_assignment_title
        )

    def recommend_reviewers(
        self,
        num_required_assignments: int,
        reviewer_assignment_title: Optional[str] = None,
        dry_run: bool = False
    ):
        return self.assignments_builder.recommend_assignments(
            group_id=self.venue.get_reviewers_id(),
            num_required_assignments=num_required_assignments,
            assignment_title=reviewer_assignment_title,
            dry_run=dry_run
        )

    def recommend_acs(
        self,
        num_required_assignments: int,
        ac_assignment_title: Optional[str] = None,
        dry_run: bool = False
    ):
        return self.assignments_builder.recommend_assignments(
            group_id=self.venue.get_area_chairs_id(),
            num_required_assignments=num_required_assignments,
            assignment_title=ac_assignment_title,
            dry_run=dry_run
        )

    #endregion ====== End of Workflow functions ======


    #region ====== Helper functions ======

    def compute_reviewer_conflicts(
        self,
        num_years: int,
        dry_run: bool = False
    ):
        return self.assignments_builder.compute_conflicts(
            group_id=self.venue.get_reviewers_id(),
            num_years=num_years,
            dry_run=dry_run
        )

    def compute_ac_conflicts(
        self,
        num_years: int,
        dry_run: bool = False
    ):
        return self.assignments_builder.compute_conflicts(
            group_id=self.venue.get_area_chairs_id(),
            num_years=num_years,
            dry_run=dry_run
        )

    def compute_sac_conflicts(
        self,
        num_years: int,
        dry_run: bool = False
    ):
        return self.assignments_builder.compute_conflicts(
            group_id=self.venue.get_senior_area_chairs_id(),
            num_years=num_years,
            dry_run=dry_run
        )

    def compute_reviewer_affinity_scores(
        self,
        dry_run: bool = False
    ):
        return self.assignments_builder.compute_affinity_scores(
            group_id=self.venue.get_reviewers_id(),
            dry_run=dry_run
        )

    def compute_ac_affinity_scores(
        self,
        dry_run: bool = False
    ):
        return self.assignments_builder.compute_affinity_scores(
            group_id=self.venue.get_area_chairs_id(),
            dry_run=dry_run
        )

    def compute_sac_affinity_scores(
        self,
        dry_run: bool = False
    ):
        return self.assignments_builder.compute_affinity_scores(
            group_id=self.venue.get_senior_area_chairs_id(),
            dry_run=dry_run
        )

    def sync_reviewer_loads(
        self,
        dry_run: bool = False
    ):
        return self.assignments_builder.sync_max_loads(
            group_id=self.venue.get_reviewers_id(),
            dry_run=dry_run
        )

    def sync_reviewer_tracks(
        self,
        dry_run: bool = False
    ):
        return self.assignments_builder.sync_research_areas(
            group_id=self.venue.get_reviewers_id(),
            dry_run=dry_run
        )

    def sync_ac_loads(
        self,
        dry_run: bool = False
    ):
        return self.assignments_builder.sync_max_loads(
            group_id=self.venue.get_area_chairs_id(),
            dry_run=dry_run
        )

    def sync_ac_tracks(
        self,
        dry_run: bool = False
    ):
        return self.assignments_builder.sync_research_areas(
            group_id=self.venue.get_area_chairs_id(),
            dry_run=dry_run
        )

    def sync_sac_loads(
        self,
        dry_run: bool = False
    ):
        return self.assignments_builder.sync_max_loads(
            group_id=self.venue.get_senior_area_chairs_id(),
            dry_run=dry_run
        )

    def sync_sac_tracks(
        self,
        dry_run: bool = False
    ):
        return self.assignments_builder.sync_research_areas(
            group_id=self.venue.get_senior_area_chairs_id(),
            dry_run=dry_run
        )

    #endregion ====== End of Helper functions ======





    # structural ideas
    '''
    - decorator to require user input on data deletion
    - helpers for grouping by head/tail and label
    - consistent label management (e.g., 'rev-matching-1' → 'rev-matching-2')
    - consistent readers/nonreaders on proposed edges
    '''

    # pre-matching
    '''
    1) registration actions
    - registering authors as reviewers
    - shifting from one role to another (ac to reviewer)
    - posting availability for profiles
    - import SAC lists from CSV and validate against profiles
    - map ACs/SACs to tracks from registration forms
    - validate track names with fuzzy matching suggestions
    - configure submission forms, hide/show fields via meta invitation
    2) run arr setup matching scripts
    - delete/reset edges (conflicts, affinity scores) when re-running setup
    - setup_committee_matching for Reviewers/ACs with chosen scorers
    - seed or reset Custom_Max_Papers (CMP) as baseline
    3) check for ac/reviewer capacity via naive matching
    - compute loads against CMP and availability notes
    - quick capacity audit before expensive matching
    '''
    # mid-matching
    '''
    1) run sac-ac matching
    - various clean up and retry logic
    - ensure SAC↔AC assignments respect COIs and track constraints
    - detect ACs with paper assignments but no SAC (debug helper)
    2) run reviewer matching
    - produce Proposed_Assignment edges for multiple labels (iterations)
    - carry over a subset of Proposed_Assignment edges across labels
    - rebuild readers/nonreaders on Proposed_Assignment edges if needed
    3) run partial matchings
    - easy interface to post 0 load custom user demands
    - automatically adjust shared cmp while grounding to notes
    - fill per-paper gaps to target (e.g., fill to 3) using CUD edges
    - move assignments between users to rebalance loads
    - clear or prune Proposed_Assignment edges by label/head/tail
    - support a secondary CMP channel (e.g., Custom_Max_Papers_2)
    '''
    # post-matching
    '''
    1) find reviewer assignments
    - convert Proposed_Assignment → Assignment edges by committee
    2) sanity checks
    - COI coverage, min-per-paper, max-load violations, group membership
    - tracks without SACs; ACs with papers but without SAC
    3) removing reviewer assignments
    - targeted cleanup utilities (by label, by user, by head)
    - snapshot + rollback helpers for edge changes
    '''
