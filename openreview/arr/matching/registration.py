import datetime
import openreview
from decorators import require_confirmation
from typing import Dict, List, Optional, Callable, Union
from note_utils import NoteUtils
from profile_utils import ProfileUtils
from copy import deepcopy

from constants import (
    PROFILE_ID_FIELD,
    REGISTRATION_FORM_MAPPING,
    LICENSE_FORM_MAPPING,
    EMERGENCY_FORM_MAPPING,
    LOAD_FORM_MAPPING,
    DEFAULT_REGISTRATION_CONTENT,
    DEFAULT_EMERGENCY_CONTENT
)


class RegistrationBuilder(object):
    def __init__(
        self,
        arr_matcher,
    ):
        self.client = arr_matcher.client
        self.venue = arr_matcher.venue

    #region ====== Registration note functions ======
    # Registration notes are any notes posted to a note invitation
    # of the form {role_id}/-/{invitation_name}

    def post_generic_registration_notes(
        self,
        invitation: str,
        profiles: List[openreview.Profile],
        profile_ids_to_raw_content: Dict[str, Dict],
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Wrapper function to post SAC registration notes."""
        default_content = deepcopy(DEFAULT_REGISTRATION_CONTENT)
        content_field_map = {
            "languages_studied": "languages_studied",
            'research_area': 'research_area',
            'priority_research_area': 'priority_research_area'
        }
        field_exceptions = None
        return self.post_registration_notes(
            invitation=invitation,
            profiles=profiles,
            profile_ids_to_raw_content=profile_ids_to_raw_content,
            default_content=default_content,
            content_field_map=content_field_map,
            field_exceptions=field_exceptions,
            dry_run=dry_run
        )

    def post_ac_reviewer_registration_notes(
        self,
        invitation: str,
        profiles: List[openreview.Profile],
        profile_ids_to_raw_content: Dict[str, Dict],
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Wrapper function to post AC/reviewer registration notes."""
        field_exceptions = None
        default_content = deepcopy(DEFAULT_REGISTRATION_CONTENT)
        content_field_map = REGISTRATION_FORM_MAPPING
        return self.post_registration_notes(
            invitation=invitation,
            profiles=profiles,
            profile_ids_to_raw_content=profile_ids_to_raw_content,
            default_content=default_content,
            content_field_map=content_field_map,
            field_exceptions=field_exceptions,
            dry_run=dry_run
        )

    def post_ac_reviewer_license_notes(
        self,
        invitation: str,
        profiles: List[openreview.Profile],
        profile_ids_to_raw_content: Dict[str, Dict],
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Wrapper function to post reviewer license notes."""
        field_exceptions = None
        default_content = {}
        content_field_map = LICENSE_FORM_MAPPING
        return self.post_registration_notes(
            invitation=invitation,
            profiles=profiles,
            profile_ids_to_raw_content=profile_ids_to_raw_content,
            default_content=default_content,
            content_field_map=content_field_map,
            field_exceptions=field_exceptions,
            dry_run=dry_run
        )

    def post_ac_reviewer_emergency_notes(
        self,
        invitation: str,
        profiles: List[openreview.Profile],
        profile_ids_to_raw_content: Dict[str, Dict],
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Wrapper function to post reviewer emergency notes."""
        field_exceptions = {
            'emergency_load': lambda val: int(val)
        }
        default_content = deepcopy(DEFAULT_EMERGENCY_CONTENT)
        content_field_map = EMERGENCY_FORM_MAPPING
        return self.post_registration_notes(
            invitation=invitation,
            profiles=profiles,
            profile_ids_to_raw_content=profile_ids_to_raw_content,
            default_content=default_content,
            content_field_map=content_field_map,
            field_exceptions=field_exceptions,
            dry_run=dry_run
        )

    def post_reviewer_load_notes(
        self,
        invitation: str,
        profiles: List[openreview.Profile],
        profile_ids_to_raw_content: Dict[str, Dict],
        default_load: int = None,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Wrapper function to post reviewer load notes."""
        if default_load is None:
            raise ValueError("default_load is required")
        field_exceptions = {
            'meta_data_donation': lambda val: (
                "No, I do not consent to donating anonymous metadata of my review for research."
                if 'no' in val.lower() else
                "Yes, I consent to donating anonymous metadata of my review for research."
            )
        }
        default_content = {
            'maximum_load_this_cycle': { 'value': default_load },
            'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' }
        }
        content_field_map = LOAD_FORM_MAPPING
        return self.post_registration_notes(
            invitation=invitation,
            profiles=profiles,
            profile_ids_to_raw_content=profile_ids_to_raw_content,
            default_content=default_content,
            content_field_map=content_field_map,
            field_exceptions=field_exceptions,
            dry_run=dry_run
        )

    def post_ac_load_notes(
        self,
        invitation: str,
        profiles: List[openreview.Profile],
        profile_ids_to_raw_content: Dict[str, Dict],
        default_load: int = None,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Wrapper function to post reviewer load notes."""
        if default_load is None:
            raise ValueError("default_load is required")
        field_exceptions = None
        default_content = {
            'maximum_load_this_cycle': { 'value': default_load },
            'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' }
        }
        content_field_map = None
        return self.post_registration_notes(
            invitation=invitation,
            profiles=profiles,
            profile_ids_to_raw_content=profile_ids_to_raw_content,
            default_content=default_content,
            content_field_map=content_field_map,
            field_exceptions=field_exceptions,
            dry_run=dry_run
        )

    def transfer_to_reviewer_load_notes(
        self,
        invitation: str,
        profiles: List[openreview.Profile],
        profile_ids_to_raw_content: Dict[str, Dict],
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Wrapper function to transfer reviewer load notes from AC load notes."""
        if not isinstance(default_load, int) or default_load <= 0:
            raise ValueError(f"default_load must be a positive integer, got: {default_load}")
        field_exceptions = None
        default_content = {
            'maximum_load_this_cycle': { 'value': default_load },
            'meta_data_donation': "No, I do not consent to donating anonymous metadata of my review for research."
        }
        content_field_map = {
            'maximum_load_this_cycle': 'maximum_load_this_cycle',
            'maximum_load_this_cycle_for_resubmissions': 'maximum_load_this_cycle_for_resubmissions'
        }
        return self.post_registration_notes(
            invitation=invitation,
            profiles=profiles,
            profile_ids_to_raw_content=profile_ids_to_raw_content,
            default_content=default_content,
            content_field_map=content_field_map,
            field_exceptions=field_exceptions,
            dry_run=dry_run
        )

    def transfer_to_ac_load_notes(
        self,
        invitation: str,
        profiles: List[openreview.Profile],
        profile_ids_to_raw_content: Dict[str, Dict],
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Wrapper function to post reviewer load notes."""
        if not isinstance(default_load, int) or default_load <= 0:
            raise ValueError(f"default_load must be a positive integer, got: {default_load}")
        field_exceptions = None
        default_content = {
            'maximum_load_this_cycle': { 'value': default_load },
            'maximum_load_this_cycle_for_resubmissions': { 'value': 'No' }
        }
        content_field_map = {
            'maximum_load_this_cycle': 'maximum_load_this_cycle',
            'maximum_load_this_cycle_for_resubmissions': 'maximum_load_this_cycle_for_resubmissions'
        }
        return self.post_registration_notes(
            invitation=invitation,
            profiles=profiles,
            profile_ids_to_raw_content=profile_ids_to_raw_content,
            default_content=default_content,
            content_field_map=content_field_map,
            field_exceptions=field_exceptions,
            dry_run=dry_run
        )

    @require_confirmation
    def post_registration_notes(
        self,
        invitation: str,
        profiles: List[openreview.Profile],
        profile_ids_to_raw_content: Dict[str, Dict],
        default_content: Dict[str, str],
        content_field_map: Dict[str, str],
        field_exceptions: Optional[Dict[str, Callable[[Dict], Dict]]] = None,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Posts registration notes for a given list of profiles and raw content.

        The raw content needs to get mapped to the destination invitation's content fields.

        This is done in 3 phases:
        1) Initialize the content from a default value
        2) Map the raw content to the destination invitation via the provided mapping
        3) If the field needs an exception for special handling, apply the exception function

        Args:
            invitation: The invitation to post registration notes to.
            profiles: List of profiles to post registration notes for.
            profile_ids_to_raw_content: Dictionary mapping profile IDs to raw content.
            default_content: Dictionary mapping content field names to default values.
            content_field_map: Dictionary mapping content field names to the field names in the destination invitation.
            field_exceptions: Optional dictionary mapping destination field names to transformation functions. 
                Each function receives the source field value and returns transformed value. Used for special 
                cases to transform the source value to the destination value.

                Example: { 'DBLP': lambda val: 'Yes', }
            profile_ids_to_raw_content: Dictionary mapping profile IDs to raw content.
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation:
            - registration_notes_posted: Number of registration notes that were posted
            - registration_notes_edited: Number of registration notes that were edited
        """
        posted, edited = 0, 0
        # Load existing data to detect duplicates
        registration_notes: List[openreview.api.Note] = self.client.get_all_notes(
            invitation=invitation
        )
        profile_name_to_note: Dict[str, openreview.api.Note] = NoteUtils.map_profile_names_to_note(
            self.client,
            registration_notes
        )

        # Map profile names to profile IDs and build valid content
        profile_name_to_id: Dict[str, str] = ProfileUtils.map_profile_names_to_profile_id(profiles)
        profile_ids_to_valid_content: Dict[str, Dict] = self._build_note_content(
            profile_ids_to_raw_content,
            default_content,
            content_field_map,
            field_exceptions=field_exceptions
        )

        # Post new notes or edit existing ones
        for profile_id, valid_content in profile_ids_to_valid_content.items():
            # Store profile ID in valid content
            valid_content[PROFILE_ID_FIELD] = {'value': profile_id}

            note = profile_name_to_note.get(profile_id, None)
            if note is None:
                posted += 1
                if not dry_run:
                    self.client.post_note_edit(
                        invitation=invitation,
                        signatures=[self.venue.id],
                        note=openreview.api.Note(
                            content=valid_content
                        )
                    )
            else:
                edited += 1
                if not dry_run:
                    self.client.post_note_edit(
                        invitation=self.venue.get_meta_invitation_id(),
                        readers=[self.venue.id],
                        writers=[self.venue.id],
                        signatures=[self.venue.id],
                        note=openreview.api.Note(
                            id=note.id,
                            content=valid_content
                        )
                    )
        
        return {
            f'{invitation.replace(self.venue.id, "")}_notes_posted': posted,
            f'{invitation.replace(self.venue.id, "")}_notes_edited': edited
        }

    def _build_note_content(
        self,
        profile_ids_to_raw_content: Dict[str, Dict],
        default_content: Dict[str, Dict],
        content_field_map: Dict[str, str],
        field_exceptions: Optional[Dict[str, Callable[[Dict], Dict]]] = None
    ) -> Dict[str, Dict]:
        """Builds a dictionary mapping profiles IDs to valid note content.

        Used for building valid content given a dictionary loaded with data from another form.

        Args:
            profile_ids_to_raw_content: Dictionary mapping profile IDs to raw content.
            content_field_map: Dictionary mapping content field names to the field names in the destination invitation.
                Fields with the same name should map to themselves (e.g., {'agreement': 'agreement'}).
            field_exceptions: Optional dictionary mapping destination field names to transformation functions. 
                Each function receives the source field value and returns transformed value. Used for special 
                cases like DBLP/Semantic Scholar that always become {'value': 'Yes'} regardless of source value.

                Example: { 'DBLP': lambda val: {'value': 'Yes'}, }
        
        Returns:
            Dictionary mapping profile IDs to valid note content.
        """
        # Extract allowed fields from invitation if provided
        allowed_fields = None
        
        result = {}
        
        for profile_id, raw_content in profile_ids_to_raw_content.items():
            mapped_content = deepcopy(default_content)
            
            # Apply content_field_map to transform field names
            if content_field_map is not None:
                for source_key, dest_key in content_field_map.items():
                    if source_key in raw_content:
                        source_value = raw_content[source_key]['value']
                        
                        # Check if there's an exception handler for this destination field
                        if field_exceptions and dest_key in field_exceptions:
                            transformed_value = field_exceptions[dest_key](source_value)
                            mapped_content[dest_key] = { 'value': transformed_value }
                        else:
                            # Copy field value directly
                            mapped_content[dest_key] = { 'value': source_value }
            
            result[profile_id] = mapped_content
        
        return result

    @require_confirmation
    def clear_registration_notes(
        self,
        invitation: str,
        valid_signatures: List[str],
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Soft deletes (sets a ddate) all registration notes that aren't in the valid signatures list.
        
        Args:
            invitation: The invitation to clear registration notes from.
            valid_signatures: List of signatures to keep.
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation:
            - registration_notes_deleted: Number of registration notes that were deleted
            - registration_notes_existing: Number of registration notes that already existed but edited
        """
        deleted, existing = 0, 0
        registration_notes: List[openreview.api.Note] = self.client.get_all_notes(
            invitation=invitation
        )
        now: int = int(datetime.datetime.now().timestamp() * 1000)

        for note in registration_notes:
            # Skip notes that are already deleted
            if note.ddate is not None:
                continue

            # Load name from note or profile ID
            signature = note.signatures[0]
            if PROFILE_ID_FIELD in note.content:
                signature = note.content[PROFILE_ID_FIELD]['value']

            if signature not in valid_signatures:
                if not dry_run:
                    self.client.post_note_edit(
                        invitation=self.venue.get_meta_invitation_id(),
                        readers=[self.venue.id],
                        writers=[self.venue.id],
                        signatures=[self.venue.id],
                        note=openreview.api.Note(
                            id=note.id,
                            ddate=now
                        )
                    )
                deleted += 1
            else:
                existing += 1
        return {
            'registration_notes_deleted': deleted,
            'registration_notes_existing': existing
        }

    #endregion ====== Registration note functions ======

    def _get_role_posting_functions(self, role: str) -> Dict[str, Callable]:
        """
        Returns a dictionary mapping form types to their role-specific posting functions.
        
        Args:
            role: The role name ('reviewer', 'area_chair', 'senior_area_chair', etc.)
        
        Returns:
            Dictionary mapping form types to posting functions:
            {
                'registration': callable,
                'license': callable,
                'emergency': callable,
                'load': callable
            }
        """
        role_configs = {
            '/Reviewers': {
                'registration': self.post_ac_reviewer_registration_notes,
                'license': self.post_ac_reviewer_license_notes,
                'emergency': self.post_ac_reviewer_emergency_notes,
                'load': self.post_reviewer_load_notes,
                'registration_invitation': f"{role}/-/Registration",
                'license_invitation': f"{role}/-/License_Agreement",
                'emergency_invitation': f"{role}/-/Emergency_Reviewer_Agreement",
                'load_invitation': f"{role}/-/Max_Load_And_Unavailability_Request",
                'transfer_load': self.transfer_to_reviewer_load_notes,
                'transfer_registration': self.post_generic_registration_notes,
            },
            '/Area_Chairs': {
                'registration': self.post_ac_reviewer_registration_notes,
                'license': self.post_ac_reviewer_license_notes,
                'emergency': self.post_ac_reviewer_emergency_notes,
                'load': self.post_ac_load_notes,
                'registration_invitation': f"{role}/-/Registration",
                'license_invitation': f"{role}/-/Metareview_License_Agreement",
                'emergency_invitation': f"{role}/-/Emergency_Metareviewer_Agreement",
                'load_invitation': f"{role}/-/Max_Load_And_Unavailability_Request",
                'transfer_load': self.transfer_to_ac_load_notes,
                'transfer_registration': self.post_generic_registration_notes,
            }
        }
        
        for suffix, functions in role_configs.items():
            if role.endswith(suffix):
                return functions
        raise ValueError(f"Unknown role: {role}. Supported roles: {list(role_configs.keys())}")

    def migrate_authors_to_role(
        self,
        author_tilde_ids: List[str],
        target_group_id: str,
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Migrates authors to a reviewing role by copying their forms to the target group and reviewer forms.

        Authors must have a research area provided or they will be skipped, this field is required for registration.
        This process will fail if any provided author does not have a profile.
        This process will fail if default_load is not a positive integer.

        Args:
            author_tilde_ids: List of author profile IDs to migrate to the target role
            target_group_id: The ID of the group to shift to.
            default_load: Default load for the target role
            dry_run: If True, skip confirmation prompt and return without making changes
        
        Returns:
            Dictionary containing statistics about the operation
        """

        if not isinstance(default_load, int) or default_load <= 0:
            raise ValueError(f"default_load must be a positive integer, got: {default_load}")

        profiles: List[openreview.Profile] = ProfileUtils.get_valid_profiles(self.client, author_tilde_ids)
        posting_functions = self._get_role_posting_functions(target_group_id)

        # Load all relevant forms and get profile IDs for avoiding duplicates
        author_forms = self.client.get_all_notes(
            invitation=f"{self.venue.get_authors_id()}/-/Submitted_Author_Form"
        )
        registration_forms = self.client.get_all_notes(
            invitation=posting_functions['registration_invitation']
        )
        license_forms = self.client.get_all_notes(
            invitation=posting_functions['license_invitation']
        )
        load_forms = self.client.get_all_notes(
            invitation=posting_functions['load_invitation']
        )
        emergency_forms = self.client.get_all_notes(
            invitation=posting_functions['emergency_invitation']
        )
        target_group = self.client.get_group(target_group_id)
        author_group = self.client.get_group(self.venue.get_authors_id())
        registration_ids = NoteUtils.get_profile_ids_from_notes(self.client, registration_forms)
        license_ids = NoteUtils.get_profile_ids_from_notes(self.client, license_forms)
        load_ids = NoteUtils.get_profile_ids_from_notes(self.client, load_forms)
        emergency_ids = NoteUtils.get_profile_ids_from_notes(self.client, emergency_forms)
        
        # Filter author forms by author_tilde_ids
        all_tilde_author_names_to_profile_id = ProfileUtils.map_profile_names_to_profile_id(profiles)
        all_tilde_author_names = list(all_tilde_author_names_to_profile_id.keys())
        author_name_to_all_names = ProfileUtils.map_profile_names_to_all_names(profiles)
        filtered_author_forms = [
            form for form in author_forms
            if form.signatures[0] in all_tilde_author_names
        ]
        profile_name_to_note = NoteUtils.map_profile_names_to_note(
            self.client,
            filtered_author_forms
        )

        # Build author data to post
        authors_processed, authors_skipped, authors_not_in_author_group, authors_no_research_areas, authors_already_in_target_role = 0, 0, 0, 0, 0
        author_to_registration = {}
        author_to_license = {}
        author_to_emergency = {}
        author_to_load = {}
        for author in author_tilde_ids:
            author_note = profile_name_to_note.get(author, None)
            author_profile_id = all_tilde_author_names_to_profile_id[author] # guaranteed by get_valid_profiles
            if author_note is None:
                authors_skipped += 1
                continue
            if not any(name in author_group.members for name in all_names):
                authors_not_in_author_group += 1
                continue
            if 'indicate_your_research_areas' not in author_note.content or \
                len(author_note.content['indicate_your_research_areas']['value']) == 0:
                authors_no_research_areas += 1
                continue
            all_names = author_name_to_all_names[author]
            if any(name in target_group.members for name in all_names):
                authors_already_in_target_role += 1
                continue

            self.add_member_to_group(
                target_group_id,
                author_profile_id,
                dry_run=dry_run
            )

            # Check for emergency load
            try:
                emergency_load = int(author_note.content.get('indicate_emergency_reviewer_load', {}).get('value', 'N/A'))
            except (ValueError, TypeError):
                emergency_load = 0

            # Prepare data to post in bulk
            if author_profile_id not in registration_ids:
                author_to_registration[author_profile_id] = author_note.content
            if author_profile_id not in license_ids:
                author_to_license[author_profile_id] = author_note.content
            if author_profile_id not in emergency_ids and emergency_load > 0:
                author_to_emergency[author_profile_id] = author_note.content
            if author_profile_id not in load_ids:
                author_to_load[author_profile_id] = author_note.content

            authors_processed += 1

        # Call to post data
        results = {}
    
        # Registration
        if posting_functions['registration'] and author_to_registration:
            results.update(posting_functions['registration'](
                invitation=posting_functions['registration_invitation'],
                profiles=profiles,
                profile_ids_to_raw_content=author_to_registration,
                dry_run=dry_run
            ))
        # License
        if posting_functions['license'] and author_to_license:
            results.update(posting_functions['license'](
                invitation=posting_functions['license_invitation'],
                profiles=profiles,
                profile_ids_to_raw_content=author_to_license,
                dry_run=dry_run
            ))
        # Emergency
        if posting_functions['emergency'] and author_to_emergency:
            results.update(posting_functions['emergency'](
                invitation=posting_functions['emergency_invitation'],
                profiles=profiles,
                profile_ids_to_raw_content=author_to_emergency,
                dry_run=dry_run
            ))
        # Load
        if posting_functions['load'] and author_to_load:
            results.update(posting_functions['load'](
                invitation=posting_functions['load_invitation'],
                profiles=profiles,
                profile_ids_to_raw_content=author_to_load,
                default_load=default_load,
                dry_run=dry_run
            ))
        
        # Build return stats
        return_stats = {
            'authors_processed': authors_processed,
            'authors_skipped': authors_skipped,
            'authors_no_research_areas': authors_no_research_areas,
            'authors_already_in_target_role': authors_already_in_target_role,
            'authors_not_in_author_group': authors_not_in_author_group
        }
        return_stats.update(results)
        return return_stats

    def shift_roles(
        self,
        tilde_ids: List[str],
        source_group_id: str,
        target_group_id: str,
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Shifts roles from one group to another while setting their load and registration.

        Args:
            tilde_ids: List of tilde IDs to shift.
            source_group_id: The ID of the group to shift from.
            target_group_id: The ID of the group to shift to.
            default_load: The default load for the target group.
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation:
            - members_shifted: Number of members that were shifted from one group to another
        """
        if not isinstance(default_load, int) or default_load <= 0:
            raise ValueError(f"default_load must be a positive integer, got: {default_load}")

        profiles: List[openreview.Profile] = ProfileUtils.get_valid_profiles(self.client, tilde_ids)
        profile_ids = [profile.id for profile in profiles]
        user_name_to_all_names = ProfileUtils.map_profile_names_to_all_names(profiles)
        posting_functions = self._get_role_posting_functions(target_group_id)

        # Load all relevant forms and get profile IDs for avoiding duplicates
        source_registration_forms = self.client.get_all_notes(
            invitation=f"{source_group_id}/-/Registration"
        )
        source_load_forms = self.client.get_all_notes(
            invitation=f"{source_group_id}/-/Max_Load_And_Unavailability_Request"
        )
        target_registration_forms = self.client.get_all_notes(
            invitation=f"{target_group_id}/-/Registration"
        )
        target_load_forms = self.client.get_all_notes(
            invitation=f"{target_group_id}/-/Max_Load_And_Unavailability_Request"
        )
        source_group = self.client.get_group(source_group_id)
        target_group = self.client.get_group(target_group_id)
        
        name_to_source_registration_note = NoteUtils.map_profile_names_to_note(
            self.client,
            source_registration_forms
        )
        name_to_source_load_note = NoteUtils.map_profile_names_to_note(
            self.client,
            source_load_forms
        )
        name_to_target_registration_note = NoteUtils.map_profile_names_to_note(
            self.client,
            target_registration_forms
        )
        name_to_target_load_note = NoteUtils.map_profile_names_to_note(
            self.client,
            target_load_forms
        )

        members_already_in_target_role = 0
        members_processed = 0
        members_skipped = 0
        notes_to_delete = []
        user_to_registration_note = {}
        user_to_load_note = {}
        for profile_id in profile_ids:
            source_registration_note = name_to_source_registration_note.get(profile_id, None)
            source_load_note = name_to_source_load_note.get(profile_id, None)
            target_registration_note = name_to_target_registration_note.get(profile_id, None)
            target_load_note = name_to_target_load_note.get(profile_id, None)

            all_names = user_name_to_all_names[profile_id]
            if any(name in target_group.members for name in all_names):
                members_already_in_target_role += 1
                continue
            if not any(name in source_group.members for name in all_names):
                members_skipped += 1
                continue

            # Update group membership
            self.remove_member_from_group(
                source_group_id,
                profile_id,
                dry_run=dry_run
            )
            self.add_member_to_group(
                target_group_id,
                profile_id,
                dry_run=dry_run
            )

            if source_registration_note is not None:
                notes_to_delete.append(source_registration_note)
            if source_load_note is not None:
                notes_to_delete.append(source_load_note)

            if target_registration_note is None:
                user_to_registration_note[profile_id] = source_registration_note.content if source_registration_note is not None else None
            if target_load_note is None:
                user_to_load_note[profile_id] = source_load_note.content if source_load_note is not None else None

            members_processed += 1

        # Call to post data
        results = {}
    
        # Registration
        if posting_functions['transfer_registration'] and user_to_registration_note:
            results.update(posting_functions['transfer_registration'](
                invitation=posting_functions['registration_invitation'],
                profiles=profiles,
                profile_ids_to_raw_content=user_to_registration_note,
                dry_run=dry_run
            ))
        # Load
        if posting_functions['transfer_load'] and user_to_load_note:
            results.update(posting_functions['transfer_load'](
                invitation=posting_functions['load_invitation'],
                profiles=profiles,
                profile_ids_to_raw_content=user_to_load_note,
                default_load=default_load,
                dry_run=dry_run
            ))
        
        # Delete notes
        if notes_to_delete:
            results.update(NoteUtils.bulk_delete_notes(
                self.client,
                self.venue,
                notes_to_delete,
                dry_run=dry_run
            ))

        # Build return stats
        return_stats = {
            'members_processed': members_processed,
            'members_already_in_target_role': members_already_in_target_role,
            'members_skipped': members_skipped
        }
        return_stats.update(results)
        return return_stats

    def make_users_available(
        self,
        tilde_ids: List[str],
        group_id: str,
        default_load: int,
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Makes users available by posting a load note.

        Args:
            tilde_ids: List of tilde IDs to make available.
            group_id: The ID of the group to make the users available to.
            default_load: The default load for the group.
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation:
            - members_made_available: Number of members that were made available
        """
        if not isinstance(default_load, int) or default_load <= 0:
            raise ValueError(f"default_load must be a positive integer, got: {default_load}")

        profiles: List[openreview.Profile] = ProfileUtils.get_valid_profiles(self.client, tilde_ids)
        profile_ids = [profile.id for profile in profiles]
        user_name_to_all_names = ProfileUtils.map_profile_names_to_all_names(profiles)
        
        posting_functions = self._get_role_posting_functions(group_id)

        # Load all relevant forms and get profile IDs for avoiding duplicates
        load_forms = self.client.get_all_notes(
            invitation=f"{group_id}/-/Max_Load_And_Unavailability_Request"
        )
        target_group = self.client.get_group(group_id)
        
        name_to_load_note = NoteUtils.map_profile_names_to_note(
            self.client,
            load_forms
        )

        members_processed = 0
        members_already_available = 0
        members_not_in_group = 0
        user_to_load_note = {}
        for profile_id in profile_ids:
            all_names = user_name_to_all_names[profile_id]
            if not any(name in target_group.members for name in all_names):
                members_not_in_group += 1
                continue
            load_note = name_to_load_note.get(profile_id, None)
            if load_note is not None:
                members_already_available += 1
                continue

            user_to_load_note[profile_id] = {
                'meta_data_donation': "No, I do not consent to donating anonymous metadata of my review for research.",
            }
            members_processed += 1

        # Call to post data
        results = {}

        # Load
        if posting_functions['load'] and user_to_load_note:
            results.update(posting_functions['load'](
                invitation=posting_functions['load_invitation'],
                profiles=profiles,
                profile_ids_to_raw_content=user_to_load_note,
                default_load=default_load,
                dry_run=dry_run
            ))

        # Build return stats
        return_stats = {
            'members_processed': members_processed,
            'members_already_available': members_already_available,
            'members_not_in_group': members_not_in_group
        }
        return_stats.update(results)
        return return_stats

    def add_member_to_group(self, group_id: str, profile_id: str, dry_run: bool = False) -> Dict[str, int]:
        """Adds a member to a group.

        Args:
            group_id: The ID of the group to add the member to.
            profile_id: The ID of the profile to add to the group.
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation:
            - members_added: Number of members that were added to the group
        """
        group = self.client.get_group(group_id)
        if profile_id not in group.members:
            if not dry_run:
                self.client.add_members_to_group(group, profile_id)
        return {
            'members_added': 1 if profile_id not in group.members else 0
        }

    def remove_member_from_group(self, group_id: str, profile_id: str, dry_run: bool = False) -> Dict[str, int]:
        """Removes a member from a group.

        Args:
            group_id: The ID of the group to remove the member from.
            profile_id: The ID of the profile to remove from the group.
            dry_run: If True, skip confirmation prompt and return without making changes

        Returns:
            Dictionary containing statistics about the operation:
            - members_removed: Number of members that were removed from the group
        """
        group = self.client.get_group(group_id)
        if profile_id in group.members:
            if not dry_run:
                self.client.remove_members_from_group(group, profile_id)
        return {
            'members_removed': 1 if profile_id in group.members else 0
        }

