import openreview

from profile_utils import ProfileUtils
from typing import Dict, List, Optional, Set, Tuple
from openreview.stages.arr_content import arr_tracks
# check conflicts
# check max loads
#   - check note -> edge
#   - check edge -> asms

class SanityChecker(object):
    def __init__(
        self,
        arr_matcher
    ):
        self.client = arr_matcher.client
        self.venue = arr_matcher.venue

    def run_sanity_checks(self):
        # check acs and reviewers
        self.check_max_loads_against_cmp()

        # check once all papers
        self.check_papers_below_min_assignments()

        # check acs and reviewers
        self.check_assignments_atmost_max_load()
    
        # check sac ac mapping
        self.check_role_mapping_mapping()

        # check all roles
        self.check_no_conflicts()

        # check role overlap
        self.check_role_overlap()

    def check_max_loads_against_cmp(
        self,
        committee_group_id: str,
        label: str
    ) -> Dict[str, Tuple[int, int]]:
        """Compare current proposed loads vs Custom_Max_Papers (and secondary CMP if used).

        Returns mapping user → (current, max).
        """
        raise NotImplementedError

    def check_papers_at_required_assignments(
        self,
        label: str,
        target_per_paper: int
    ) -> List[str]:
        """List submission ids with fewer than `target_per_paper` Proposed_Assignments under `label`."""
        raise NotImplementedError

    def check_assignments_atmost_max_load(self):
        pass

    def check_assignments_atmost_target_load(self):
        pass

    def check_role_mapping_mapping(self):
        pass

    def check_no_conflicts(self):
        pass
    
    def check_role_overlap(
        self,
        first_group_id: str,
        second_group_id: str
    ) -> Dict[str, int]:
        """Checks if there is any overlap between the two groups.

        Args:
            first_group_id: The ID of the first group.
            second_group_id: The ID of the second group.

        Returns:
            Dictionary containing statistics about the operation
            - members_in_overlap: Number of members that are in both groups
        """
        first_group = self.client.get_group(first_group_id)
        second_group = self.client.get_group(second_group_id)
        members_in_overlap = len(set(first_group.members) & set(second_group.members))
        members_not_in_overlap = len(set(first_group.members) - set(second_group.members))
        members_not_in_first_group = len(set(second_group.members) - set(first_group.members))
        members_not_in_second_group = len(set(first_group.members) - set(second_group.members))
        return {
            'members_in_overlap': members_in_overlap,
            'members_not_in_overlap': members_not_in_overlap,
            'members_not_in_first_group': members_not_in_first_group,
            'members_not_in_second_group': members_not_in_second_group
        }

    def check_edge_group_synchronization(self):
        pass

    def check_valid_tracks(self, tracks: List[str]) -> bool:
        """Checks if all tracks are valid ARR tracks."""
        for track in tracks:
            if track not in arr_tracks:
                raise ValueError(f"Invalid track: {track}")
        return True
    