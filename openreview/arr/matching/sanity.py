import openreview

from note_utils import NoteUtils
from profile_utils import ProfileUtils
from edge_utils import EdgeUtils, EdgeGroupBy
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

    def run_sanity_checks(
        self,
        sac_assignment_title: Optional[str] = None,
        ac_assignment_title: Optional[str] = None,
        reviewer_assignment_title: Optional[str] = None
    ):
        results = {}
        role_titles = {
            self.venue.get_senior_area_chairs_id(): sac_assignment_title,
            self.venue.get_area_chairs_id(): ac_assignment_title,
            self.venue.get_reviewers_id(): reviewer_assignment_title
        }

        
        # check acs and reviewers
        results.update(
            self.check_max_loads_against_cmp(ac_assignment_title, reviewer_assignment_title)
        )

        # check once all papers
        results.update(
            self.check_papers_below_min_assignments(
                sac_assignment_title, ac_assignment_title, reviewer_assignment_title
            )
        )

        # check acs and reviewers
        results.update(
            self.check_assignments_atmost_max_load(ac_assignment_title, reviewer_assignment_title)
        )
    
        # check sac ac mapping
        results.update(
            self.check_sac_ac_mapping(sac_assignment_title, ac_assignment_title)
        )

        # check all roles
        for role, assignment_title in role_titles.items():
            results.update(
                self.check_no_conflicts(role, assignment_title)
            )

        # check role overlap
        results.update(
            self.check_role_overlap(
                first_group_id=self.venue.get_senior_area_chairs_id(),
                second_group_id=self.venue.get_area_chairs_id()
            )
        )
        results.update(
            self.check_role_overlap(
                first_group_id=self.venue.get_senior_area_chairs_id(),
                second_group_id=self.venue.get_reviewers_id()
            )
        )
        results.update(
            self.check_role_overlap(
                first_group_id=self.venue.get_area_chairs_id(),
                second_group_id=self.venue.get_reviewers_id()
            )
        )

        return results

    def check_max_loads_against_cmp(
        self,
        ac_assignment_title: Optional[str] = None,
        reviewer_assignment_title: Optional[str] = None
    ):
        results = {
            'ac_max_papers_exceeding_max_load_note': 0,
            'reviewer_max_papers_exceeding_max_load_note': 0
        }

        ac_custom_max_papers = EdgeUtils.get_custom_max_papers(self.client, self.venue.get_area_chairs_id(), by=EdgeGroupBy.user)
        reviewer_custom_max_papers = EdgeUtils.get_custom_max_papers(self.client, self.venue.get_reviewers_id(), by=EdgeGroupBy.user)

        ac_max_load_notes = self.client.get_all_notes(
            invitation=f"{self.venue.get_area_chairs_id()}/-/Max_Load_And_Unavailability_Request"
        )
        ac_id_to_note = NoteUtils.map_profile_id_to_note(self.client, ac_max_load_notes)
        reviewer_max_load_notes = self.client.get_all_notes(
            invitation=f"{self.venue.get_reviewers_id()}/-/Max_Load_And_Unavailability_Request"
        )
        reviewer_id_to_note = NoteUtils.map_profile_id_to_note(self.client, reviewer_max_load_notes)

        for ac_id, ac_max_papers in ac_custom_max_papers.items():
            ac_note = ac_id_to_note.get(ac_id, None)
            if ac_note is None:
                results['ac_max_papers_exceeding_max_load_note'] += 1
            else:
                ac_max_load = int(ac_note.content['maximum_load_this_cycle']['value'])
                if ac_max_papers > ac_max_load:
                    results['ac_max_papers_exceeding_max_load_note'] += 1

        for reviewer_id, reviewer_max_papers in reviewer_custom_max_papers.items():
            reviewer_note = reviewer_id_to_note.get(reviewer_id, None)
            if reviewer_note is None:
                results['reviewer_max_papers_exceeding_max_load_note'] += 1
            else:
                reviewer_max_load = int(reviewer_note.content['maximum_load_this_cycle']['value'])
                if reviewer_max_papers > reviewer_max_load:
                    results['reviewer_max_papers_exceeding_max_load_note'] += 1

        return results

    def check_papers_below_min_assignments(
        self,
        sac_assignment_title: Optional[str] = None,
        ac_assignment_title: Optional[str] = None,
        reviewer_assignment_title: Optional[str] = None
    ):
        results = {
            'sac_assignments_below_min_assignments': 0,
            'ac_assignments_below_min_assignments': 0,
            'reviewer_assignments_below_min_assignments': 0
        }
        sac_assignments = EdgeUtils.get_assignments(self.client, self.venue.get_senior_area_chairs_id(), by=EdgeGroupBy.paper, title=sac_assignment_title)
        ac_assignments = EdgeUtils.get_assignments(self.client, self.venue.get_area_chairs_id(), by=EdgeGroupBy.paper, title=ac_assignment_title)
        reviewer_assignments = EdgeUtils.get_assignments(self.client, self.venue.get_reviewers_id(), by=EdgeGroupBy.paper, title=reviewer_assignment_title)

        for paper, assigned_users in sac_assignments.items():
            if len(assigned_users) < 1:
                results['sac_assignments_below_min_assignments'] += 1
        for paper, assigned_users in ac_assignments.items():
            if len(assigned_users) < 1:
                results['ac_assignments_below_min_assignments'] += 1
        for paper, assigned_users in reviewer_assignments.items():
            if len(assigned_users) < 3:
                results['reviewer_assignments_below_min_assignments'] += 1

        return results

    def check_assignments_atmost_max_load(
        self,
        ac_assignment_title: Optional[str] = None,
        reviewer_assignment_title: Optional[str] = None
    ):
        results = {
            'ac_assignments_exceeding_max_load': 0,
            'reviewer_assignments_exceeding_max_load': 0
        }
        ac_assignments = EdgeUtils.get_assignments(self.client, self.venue.get_area_chairs_id(), by=EdgeGroupBy.user, title=ac_assignment_title)
        reviewer_assignments = EdgeUtils.get_assignments(self.client, self.venue.get_reviewers_id(), by=EdgeGroupBy.user, title=reviewer_assignment_title)

        ac_max_loads = EdgeUtils.get_custom_max_papers(self.client, self.venue.get_area_chairs_id())
        reviewer_max_loads = EdgeUtils.get_custom_max_papers(self.client, self.venue.get_reviewers_id())

        for user, assigned_papers in ac_assignments.items():
            if len(assigned_papers) > ac_max_loads.get(user, 0):
                results['ac_assignments_exceeding_max_load'] += 1
        for user, assigned_papers in reviewer_assignments.items():
            if len(assigned_papers) > reviewer_max_loads.get(user, 0):
                results['reviewer_assignments_exceeding_max_load'] += 1
        return results

    def check_sac_ac_mapping(
        self,
        sac_assignment_title: Optional[str] = None,
        ac_assignment_title: Optional[str] = None
    ):
        results = {
            'acs_with_sac_mismatch': 0
        }
        sac_assignments = EdgeUtils.get_assignments(self.client, self.venue.get_senior_area_chairs_id(), by=EdgeGroupBy.user, title=sac_assignment_title)
        ac_assignments = EdgeUtils.get_assignments(self.client, self.venue.get_area_chairs_id(), by=EdgeGroupBy.user, title=ac_assignment_title)
        ac_assignments_by_head = EdgeUtils.get_assignments(self.client, self.venue.get_area_chairs_id(), by=EdgeGroupBy.head, title=ac_assignment_title)
        for sac, assigned_papers in sac_assignments.items():
            # get acs assigned to papers that are assigned to sac
            assigned_acs = set()
            for paper in assigned_papers:
                assigned_acs.update(ac_assignments_by_head.get(paper, []))

            # assert that all papers belonging to assigned acs are assigned to sac
            papers_assigned_to_acs = set()
            for ac in assigned_acs:
                ac_assigned_papers = ac_assignments.get(ac, [])
                papers_assigned_to_acs.update(ac_assigned_papers)
            
            results['acs_with_sac_mismatch'] += len(papers_assigned_to_acs - set(assigned_papers))
        return results

    def check_no_conflicts(
        self,
        group_id: str,
        assignment_title: Optional[str] = None
    ) -> bool:

        results = {
            f'{group_id} with conflicts': 0
        }
        conflicts = EdgeUtils.get_conflicts(self.client, group_id, by=EdgeGroupBy.user)
        assignments = EdgeUtils.get_assignments(self.client, group_id, by=EdgeGroupBy.user, title=assignment_title)
        for user, assigned_papers in assignments.items():
            user_conflicts = conflicts.get(user, [])
            for paper in assigned_papers:
                if paper in user_conflicts:
                    results[f'{group_id} with conflicts'] += 1
        return results
    
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
        key = f"{first_group_id}-{second_group_id}"
        first_group = self.client.get_group(first_group_id)
        second_group = self.client.get_group(second_group_id)
        members_in_overlap = len(set(first_group.members) & set(second_group.members))
        return {
            f'{key} overlap': members_in_overlap
        }

    def check_edge_group_synchronization(
        self,
        group_id: str
    ):
        results = {
            f'{group_id} edge group mismatch': 0
        }
        all_submission_groups = self.client.get_all_groups(
            prefix=f"{self.venue.id}/Submission"
        )
        number_to_id = {
            str(submission.number): submission.id for submission in self.client.get_all_notes(
                prefix=f"{self.venue.id}/Submission"
            )
        }
        group_suffix = group_id.split('/')[-1]
        filtered_groups = [
            group
            for group in all_submission_groups if group.id.endswith(f"/{group_suffix}")
        ]
        assignments = EdgeUtils.get_assignments(self.client, group_id, by=EdgeGroupBy.head)

        for group in filtered_groups:
            number = group.id.split('/')[-2].replace('Submission', '')
            submission_id = number_to_id.get(number, None)
            if submission_id is None:
                continue
            assigned_users = assignments.get(submission_id, [])
            if set(assigned_users) != set(group.members):
                results[f'{group_id} edge group mismatch'] += 1
        return results

    def check_assignments_atmost_target_load(
        self,
        group_id: str,
        target_load: int,
        assignment_title: Optional[str] = None,
    ):
        results = {
            f'{group_id} assignments exceeding target load': 0
        }
        assignments = EdgeUtils.get_assignments(self.client, group_id, by=EdgeGroupBy.user, title=assignment_title)
        for user, assigned_papers in assignments.items():
            if len(assigned_papers) > target_load:
                results[f'{group_id} assignments exceeding target load'] += 1
        return results

    def check_valid_tracks(self, tracks: List[str]) -> bool:
        """Checks if all tracks are valid ARR tracks."""
        for track in tracks:
            if track not in arr_tracks:
                raise ValueError(f"Invalid track: {track}")
        return True
    