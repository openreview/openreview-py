"""Executable contract for current-AE access to linked prior-round records."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
HELPER = (
    ROOT
    / "site_config/python_scripts/invitations/venue/previous_submission_ae_reader_bridge.py"
)
SUBMISSION_POSTPROCESS = (
    ROOT / "site_config/python_scripts/invitations/venue/submission/postprocess.py"
)
AE_ASSIGNMENT_PROCESS = (
    ROOT / "site_config/invitations/action_editors/assignment/process_functions/process.py"
)


class Journal:
    venue_id = "JMLR"

    def get_meta_invitation_id(self):
        return "JMLR/-/Edit"

    def get_action_editors_id(self, number=None):
        return "JMLR/Action_Editors" if number is None else f"JMLR/Paper{number}/Action_Editors"

    def get_review_id(self, number):
        return f"JMLR/Paper{number}/-/Review"

    def get_ae_decision_id(self, number):
        return f"JMLR/Paper{number}/-/Decision"

    def get_author_submission_id(self):
        return "JMLR/-/Submission"


def submission(note_id, number, previous_id=None, readers=None):
    content = {}
    if previous_id:
        content["previous_JMLR_submission_url"] = {
            "value": f"https://openreview.net/forum?id={previous_id}"
        }
    return SimpleNamespace(
        id=note_id,
        number=number,
        domain="JMLR",
        invitations=["JMLR/-/Submission"],
        content=content,
        readers=list(readers or ["JMLR"]),
    )


class Client:
    def __init__(self):
        self.current = submission("current", 3, "previous")
        self.previous = submission("previous", 2, "oldest")
        self.oldest = submission("oldest", 1, "current", ["everyone"])  # cycle must terminate
        self.notes = {note.id: note for note in (self.current, self.previous, self.oldest)}
        self.reviews = {
            "previous": [SimpleNamespace(id="review-2", readers=["JMLR", "~Reviewer2"])],
            "oldest": [SimpleNamespace(id="review-1", readers=["everyone"])],
        }
        self.decisions = {
            "previous": [SimpleNamespace(id="decision-2", readers=["JMLR"])],
            "oldest": [SimpleNamespace(id="decision-1", readers=["everyone"])],
        }
        self.writes = []

    def get_note(self, note_id):
        return self.notes[note_id]

    def get_notes(self, forum, invitation):
        previous = self.notes[forum]
        if invitation == f"JMLR/Paper{previous.number}/-/Review":
            return self.reviews.get(forum, [])
        assert invitation == f"JMLR/Paper{previous.number}/-/Decision"
        return self.decisions.get(forum, [])

    def post_note_edit(self, **kwargs):
        self.writes.append(kwargs)
        edited = kwargs["note"]
        for note in self.notes.values():
            if note.id == edited.id:
                note.readers = list(edited.readers)
        for collection in (self.reviews, self.decisions):
            for notes in collection.values():
                for note in notes:
                    if note.id == edited.id:
                        note.readers = list(edited.readers)


def load_helper():
    def record(**values):
        return SimpleNamespace(**values)

    namespace = {
        "openreview": SimpleNamespace(api=SimpleNamespace(Note=record)),
    }
    exec(compile(HELPER.read_text(encoding="utf-8"), str(HELPER), "exec"), namespace)
    return namespace


def test_bridge_is_recursive_cycle_safe_idempotent_and_reader_only():
    client = Client()
    journal = Journal()
    bridge = load_helper()["ensure_previous_submission_access_for_current_ae"]

    bridge(client, journal, client.current)
    bridge(client, journal, client.current)

    assert len(client.writes) == 3
    writes = {write["note"].id: write for write in client.writes}
    assert all(write["invitation"] == "JMLR/-/Edit" for write in writes.values())
    assert all(write["signatures"] == ["JMLR"] for write in writes.values())
    assert writes["previous"]["note"].readers == [
        "JMLR",
        "JMLR/Paper3/Action_Editors",
    ]
    assert writes["decision-2"]["note"].readers == [
        "JMLR",
        "JMLR/Paper3/Action_Editors",
    ]
    assert writes["review-2"]["note"].readers == [
        "JMLR",
        "~Reviewer2",
        "JMLR/Paper3/Action_Editors",
    ]
    assert all(not hasattr(write["note"], "content") for write in writes.values())
    assert client.reviews["oldest"][0].readers == ["everyone"]


def test_invalid_or_cross_venue_previous_note_is_not_bridged():
    client = Client()
    client.previous.domain = "OtherVenue"
    bridge = load_helper()["ensure_previous_submission_access_for_current_ae"]

    bridge(client, Journal(), client.current)

    assert client.writes == []


def test_submission_and_every_ae_assignment_wire_the_shared_bridge():
    marker = "invitations/venue/previous_submission_ae_reader_bridge.py"
    call = "ensure_previous_submission_access_for_current_ae(client, journal,"
    submission = SUBMISSION_POSTPROCESS.read_text(encoding="utf-8")
    assignment = AE_ASSIGNMENT_PROCESS.read_text(encoding="utf-8")

    assert marker in submission
    assert f"{call} note)" in submission
    assert marker in assignment
    assert f"{call} submission)" in assignment
    assert assignment.index(f"{call} submission)") < assignment.index(
        "journal_process.process_update("
    )
