import openreview, time

from typing import Dict, List, Optional, Union, Literal
from decorators import require_confirmation

# parse assignment edges "by submission" or "by user"
# fetching all kinds of different edges (cmp, conflict, research_area, affinity_score, proposed_assignments, etc)


class EdgeUtils(object):

    @staticmethod
    @require_confirmation
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

    CONFIG_SUFFIXES = ['Custom_Max_Papers', 'Custom_User_Demands', 'Aggregate_Score']
    ASSIGNMENT_SUFFIXES = ['Proposed_Assignment', 'Assignment']

    @staticmethod
    def _get_role_type(
        venue: Union[openreview.venue.Venue, openreview.arr.ARR],
        invitation: str
    ) -> Optional[Literal['reviewers', 'area_chairs', 'senior_area_chairs']]:
        """Determine the role type from the invitation string."""
        if venue.get_reviewers_id() in invitation:
            return 'reviewers'
        elif venue.get_area_chairs_id() in invitation:
            return 'area_chairs'
        elif venue.get_senior_area_chairs_id() in invitation:
            return 'senior_area_chairs'
        return None

    @staticmethod
    def _get_suffix_type(invitation_suffix: str) -> Literal['config', 'assignment']:
        """Determine if the invitation suffix is a config or assignment type."""
        if any(suffix in invitation_suffix for suffix in EdgeUtils.CONFIG_SUFFIXES):
            return 'config'
        elif any(suffix in invitation_suffix for suffix in EdgeUtils.ASSIGNMENT_SUFFIXES):
            return 'assignment'
        else:
            raise ValueError(f"Unknown invitation suffix type: {invitation_suffix}")

    @staticmethod
    def _build_readers_for_role(
        venue: Union[openreview.venue.Venue, openreview.arr.ARR],
        role_type: str,
        suffix_type: str,
        tail: str,
        paper_number: Optional[int] = None
    ) -> List[str]:
        """Build readers list based on role and suffix type."""
        readers = [venue.id]
        
        if suffix_type == 'config':
            if role_type == 'reviewers':
                readers.extend([
                    venue.get_senior_area_chairs_id(),
                    venue.get_area_chairs_id()
                ])
            elif role_type == 'area_chairs':
                readers.append(venue.get_senior_area_chairs_id())
        elif suffix_type == 'assignment':
            if role_type == 'reviewers':
                readers.extend([
                    venue.get_senior_area_chairs_id(number=paper_number),
                    venue.get_area_chairs_id(number=paper_number)
                ])
            elif role_type == 'area_chairs':
                readers.append(venue.get_senior_area_chairs_id(number=paper_number))
        
        readers.append(tail)
        return readers

    @staticmethod
    def _build_writers_for_role(
        venue: Union[openreview.venue.Venue, openreview.arr.ARR],
        role_type: str,
        suffix_type: str,
        paper_number: Optional[int] = None
    ) -> List[str]:
        """Build writers list based on role and suffix type."""
        writers = [venue.id]
        
        if suffix_type == 'assignment':
            if role_type == 'reviewers':
                writers.extend([
                    venue.get_senior_area_chairs_id(number=paper_number),
                    venue.get_area_chairs_id(number=paper_number)
                ])
            elif role_type == 'area_chairs':
                writers.append(venue.get_senior_area_chairs_id(number=paper_number))
        
        return writers

    @staticmethod
    def build_readers_writers_signatures_nonreaders(
        venue: Union[openreview.venue.Venue, openreview.arr.ARR],
        invitation: str,
        tail: str,
        paper_number: Optional[int] = None
    ) -> Dict[str, List[str]]:
        """Builds the readers, writers, signatures, and nonreaders for a given edge invitation.

        Useful for edge invitations that have a different set of readers, writers, signatures, 
        and nonreaders than the venue.

        Args:
            venue: The venue or ARR instance.
            invitation: The invitation to build the readers, writers, signatures, and nonreaders for.
            tail: The tail (user/group) for the edge.
            paper_number: The paper number to build the readers, writers, signatures, and nonreaders for.
                Required for assignment-type invitations.
        
        Returns:
            A dictionary containing the readers, writers, signatures, and nonreaders.
        
        Raises:
            ValueError: If the invitation doesn't match any known role or suffix type.
        """
        invitation_suffix = invitation.split('/')[-1]
        
        role_type = EdgeUtils._get_role_type(venue, invitation)
        if role_type is None:
            raise ValueError(f"Invalid invitation: {invitation}")
        
        suffix_type = EdgeUtils._get_suffix_type(invitation_suffix)
        
        readers = EdgeUtils._build_readers_for_role(
            venue, role_type, suffix_type, tail, paper_number
        )
        writers = EdgeUtils._build_writers_for_role(
            venue, role_type, suffix_type, paper_number
        )
        
        result = {
            'readers': readers,
            'writers': writers,
            'signatures': [venue.id],
            'nonreaders': None
        }
        
        # Add nonreaders for assignment-type invitations
        if suffix_type == 'assignment':
            result['nonreaders'] = [venue.get_authors_id(number=paper_number)]
        
        return result

    @require_confirmation
    @staticmethod
    def post_bulk_edges(
        client: openreview.api.OpenReviewClient,
        edges: List,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Post edges in bulk"""
        if not dry_run:
            openreview.tools.post_bulk_edges(
                client,
                edges
            )
        return {
            'edges_posted': len(edges)
        }
    
    @require_confirmation
    @staticmethod
    def post_sequential_edges(
        client: openreview.api.OpenReviewClient,
        edges: List,
        dry_run: bool = False
    ) -> None:
        """Post edges in sequentially
        
        This runs the process function of each edge. Useful for sending notifications and
            synchronizing edges with groups
        
        """
        raise NotImplementedError
