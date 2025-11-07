import openreview

from decorators import require_confirmation
from typing import Dict, Iterable, List, Optional, Set

class ProfileUtils(object):

    @staticmethod
    @require_confirmation
    def reset_group_members(
        client: openreview.api.OpenReviewClient,
        group_id: str,
        target_members: List[str],
        dry_run: bool = False
    ):
        """Resets the members of a group to the target members."""
        group = client.get_group(group_id)
        if set(group.members) != set(target_members):
            if not dry_run:
                client.delete_members_from_group(
                    group_id,
                    group.members
                )
                client.add_members_to_group(
                    group_id,
                    target_members
                )
        return {
            'members_deleted': len(group.members) - len(target_members),
            'members_added': len(target_members) - len(group.members)
        }

    @staticmethod
    def get_valid_profiles(
        client: openreview.api.OpenReviewClient,
        profile_ids_or_emails: List[str]
    ) -> List[openreview.Profile]:
        """Fetches profiles and raises an exception if any profile is not found.
        NOTE: Any given profile ID may or may not be the canonical profile ID (profile.id).
        """
        profiles: List[openreview.Profile] = openreview.tools.get_profiles(client, profile_ids_or_emails)
        all_names: List[str] = ProfileUtils.get_all_profile_names(profiles)
        missing_names: Set[str] = set(profile_ids_or_emails) - set(all_names)
        email_only_profiles: Set[str] = {
            profile.id for profile in profiles if not profile.id.startswith('~')
        }

        if len(missing_names) > 0:
            raise ValueError(f"No profiles found for the following names: {list(missing_names)}")
        if len(email_only_profiles) > 0:
            raise ValueError(f"No profiles found for the following emails: {list(email_only_profiles)}")

        return profiles

    @staticmethod
    def get_all_profile_names(
        profiles: List[openreview.Profile]
    ) -> List[str]:
        """Returns a list of all names in all profiles."""
        all_names: List[str] = []

        for profile in profiles:
            all_names.extend(
                [
                    name_obj['username']
                    for name_obj in profile.content.get('names', [])
                    if 'username' in name_obj and len(name_obj['username']) > 0
                ]
            )

        return all_names

    @staticmethod
    def map_profile_names_to_profile_id(
        profiles: List[openreview.Profile]
    ) -> Dict[str, str]:
        """Maps any given profile name to their profile ID."""
        name_to_id: Dict[str, str] = {}

        for profile in profiles:
            for name_obj in profile.content.get('names', []):
                if 'username' in name_obj and len(name_obj['username']) > 0:
                    name_to_id[name_obj['username']] = profile.id

        return name_to_id

    @staticmethod
    def map_profile_names_to_all_names(
        profiles: List[openreview.Profile]
    ) -> Dict[str, List[str]]:
        """Maps any given profile name to all their names."""
        name_to_all_names: Dict[str, List[str]] = {}

        for profile in profiles:
            all_names = [
                name_obj['username']
                for name_obj in profile.content.get('names', [])
                if 'username' in name_obj and len(name_obj['username']) > 0
            ]
            for name in all_names:
                name_to_all_names[name] = all_names

        return name_to_all_names
