import openreview
import datetime
from profile_utils import ProfileUtils
from typing import Dict, List, Set, Union
from constants import PROFILE_ID_FIELD

from decorators import require_confirmation

class NoteUtils(object):

    @staticmethod
    def get_profile_ids_from_notes(
        client: openreview.api.OpenReviewClient,
        notes: List[openreview.api.Note]
    ) -> Set[str]:
        """Gets the profile IDs corresponding to the submitted note"""
        tilde_ids, profile_ids = [], set()
        for note in notes:
            signature = note.signatures[0]
            if PROFILE_ID_FIELD in note.content:
                signature = note.content[PROFILE_ID_FIELD]['value']
        
            tilde_ids.append(signature)

        profiles = openreview.tools.get_profiles(client, tilde_ids)
        name_to_id = ProfileUtils.map_profile_names_to_profile_id(profiles)
        profile_ids = set(
            name_to_id[tilde_id] for tilde_id in tilde_ids if tilde_id in name_to_id
        )

        return profile_ids

    @staticmethod
    def map_profile_names_to_note(
        client: openreview.api.OpenReviewClient,
        notes: List[openreview.api.Note]
    ) -> Dict[str, openreview.api.Note]:
        """Maps any given profile name to their registration note."""
        name_to_note: Dict[str, openreview.api.Note] = {}
        all_tilde_ids = []
        for note in notes:
            # Load signature from note or profile ID
            signature = note.signatures[0]
            if PROFILE_ID_FIELD in note.content:
                signature = note.content[PROFILE_ID_FIELD]['value']
            all_tilde_ids.append(signature)

        profiles = openreview.tools.get_profiles(client, all_tilde_ids)
        name_to_all_names: Dict[str, List[str]] = ProfileUtils.map_profile_names_to_all_names(profiles)

        for note in notes:
            # Load signature from note or profile ID
            signature = note.signatures[0]
            if PROFILE_ID_FIELD in note.content:
                signature = note.content[PROFILE_ID_FIELD]['value']

            signatures_names = name_to_all_names.get(signature, [signature])
            for name in signatures_names:
                name_to_note[name] = note
        return name_to_note

    @staticmethod
    @require_confirmation
    def bulk_delete_notes(
        client: openreview.api.OpenReviewClient,
        venue: Union[openreview.venue.Venue, openreview.arr.ARR],
        notes: List[openreview.api.Note],
        dry_run: bool = False
    ) -> Dict[str, int]:
        """Bulk deletes a list of notes."""
        now: int = int(datetime.datetime.now().timestamp() * 1000)
        for note in notes:
            if not dry_run:
                client.post_note_edit(
                    invitation=venue.get_meta_invitation_id(),
                    readers=[venue.id],
                    writers=[venue.id],
                    signatures=[venue.id],
                    note=openreview.api.Note(
                        id=note.id,
                        ddate=now
                    )
                )
        return {
            'notes_deleted': len(notes)
        }