"""Executable coverage for the JMLR submission postprocess delta."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
POSTPROCESS = (
    ROOT / "site_config/python_scripts/invitations/venue/submission/postprocess.py"
)


class FakeJournal:
    venue_id = "JMLR"

    def __init__(self, conflicts=()):
        self.assignment = SimpleNamespace(
            compute_conflicts=lambda _note, candidate: candidate in conflicts
        )

    def get_revision_id(self, number):
        return f"JMLR/Paper{number}/-/Revision"

    def get_meta_invitation_id(self):
        return "JMLR/-/Edit"

    def get_ae_assignment_id(self, archived=False):
        return f"JMLR/Action_Editors/-/{'Archived_Assignment' if archived else 'Assignment'}"

    def get_action_editors_id(self, number=None):
        return "JMLR/Action_Editors" if number is None else f"JMLR/Paper{number}/Action_Editors"

    def get_authors_id(self, number):
        return f"JMLR/Paper{number}/Authors"

    def get_editors_in_chief_id(self):
        return "JMLR/Editors_In_Chief"

    def get_review_id(self, number):
        return f"JMLR/Paper{number}/-/Review"

    def get_ae_decision_id(self, number):
        return f"JMLR/Paper{number}/-/Decision"

    def get_author_submission_id(self):
        return "JMLR/-/Submission"


class FakeClient:
    def __init__(self, *, previous=False, first_edit=True, conflicts=()):
        previous_url = "https://dev.openreview.net/forum?id=prior-forum-id"
        self.current = SimpleNamespace(
            id="current-forum-id",
            number=6727,
            content={
                "title": {"value": "Current"},
                **(
                    {"previous_JMLR_submission_url": {"value": previous_url}}
                    if previous
                    else {}
                ),
            },
        )
        self.previous = SimpleNamespace(
            id="prior-forum-id",
            number=123,
            domain="JMLR",
            invitations=["JMLR/-/Submission"],
            content={},
            readers=["everyone"],
        )
        self.revision = SimpleNamespace(
            edit={"note": {"content": {"track_id": {"value": "Regular"}, "title": {}}}}
        )
        self.journal = FakeJournal(conflicts)
        self.first_edit = first_edit
        self.prior_edges = []
        self.current_edges = []
        self.base_members = set()
        self.invitation_writes = []
        self.note_writes = []
        self.edge_writes = []

    def get_note(self, note_id):
        if note_id == self.current.id:
            return self.current
        if note_id == self.previous.id:
            return self.previous
        raise AssertionError(note_id)

    def get_invitation(self, invitation_id):
        assert invitation_id == "JMLR/Paper6727/-/Revision"
        return self.revision

    def post_invitation_edit(self, **kwargs):
        self.invitation_writes.append(kwargs)

    def get_note_edits(self, note_id, sort):
        assert (note_id, sort) == (self.current.id, "tcdate:asc")
        first_id = "edit-under-test" if self.first_edit else "earlier-edit"
        return [SimpleNamespace(id=first_id)]

    def post_note_edit(self, **kwargs):
        self.note_writes.append(kwargs)
        self.current.content.update(kwargs["note"].content)

    def get_edges(self, invitation, head):
        if head == self.previous.id:
            assert invitation in {
                "JMLR/Action_Editors/-/Assignment",
                "JMLR/Action_Editors/-/Archived_Assignment",
            }
            return [edge for edge in self.prior_edges if edge.invitation == invitation]
        if head == self.current.id:
            assert invitation == "JMLR/Action_Editors/-/Assignment"
            return self.current_edges
        raise AssertionError((invitation, head))

    def get_group(self, group_id):
        if group_id == "JMLR/Action_Editors":
            return SimpleNamespace(members=sorted(self.base_members))
        assert group_id in {
            "JMLR/Paper6727/Authors",
            "JMLR/Paper6727/Action_Editors",
        }
        return SimpleNamespace(members=[])

    def post_edge(self, edge):
        self.edge_writes.append(edge)

    def get_notes(self, **_kwargs):
        return []


def load_process(client):
    def record(**values):
        return SimpleNamespace(**values)

    openreview = SimpleNamespace(
        journal=SimpleNamespace(
            JournalRequest=SimpleNamespace(
                get_journal=lambda _client, _venue_id: client.journal
            )
        ),
        api=SimpleNamespace(Note=record, Edge=record),
        tools=SimpleNamespace(
            get_invitation=lambda current_client, invitation_id: current_client.get_invitation(
                invitation_id
            )
        ),
    )
    source = POSTPROCESS.read_text()
    include = "invitations/venue/previous_submission_ae_reader_bridge.py"
    helper = ROOT / "site_config/python_scripts" / include
    source = source.replace(
        f"# {{{{PYTHON_SCRIPT_FILE:{include}}}}}", helper.read_text(encoding="utf-8")
    )
    namespace = {"openreview": openreview}
    exec(compile(source, str(POSTPROCESS), "exec"), namespace)
    return namespace["process"]


def run(client):
    edit = SimpleNamespace(id="edit-under-test", note=SimpleNamespace(id=client.current.id))
    load_process(client)(client, edit, SimpleNamespace())


def prior_edge(client, candidate, tcdate, *, archived=False):
    return SimpleNamespace(
        invitation=client.journal.get_ae_assignment_id(archived=archived),
        tail=candidate,
        tcdate=tcdate,
    )


def test_every_submission_removes_track_from_revision_schema_only():
    client = FakeClient()

    run(client)

    assert "track_id" not in client.revision.edit["note"]["content"]
    assert len(client.invitation_writes) == 1
    assert client.invitation_writes[0]["invitation"] is client.revision
    assert client.invitation_writes[0]["replacement"] is True
    assert client.note_writes == []
    assert client.edge_writes == []


def test_only_the_first_submission_edit_creates_resubmission_side_effects():
    client = FakeClient(previous=True, first_edit=False)

    run(client)

    assert len(client.invitation_writes) == 1
    assert client.note_writes == []
    assert client.edge_writes == []


def test_resubmission_stores_server_link_and_assigns_newest_eligible_previous_ae():
    client = FakeClient(previous=True, conflicts={"~Conflicted1"})
    client.base_members = {"~Eligible1", "~Conflicted1"}
    client.prior_edges = [
        prior_edge(client, "~Former1", 40),
        prior_edge(client, "~Conflicted1", 30),
        prior_edge(client, "~Eligible1", 20, archived=True),
    ]

    run(client)

    expected_url = "https://dev.openreview.net/forum?id=prior-forum-id"
    assert client.current.content["previous_JMLR_submission"] == {
        "value": f"[Paper 123]({expected_url})"
    }
    assert len(client.note_writes) == 1
    assert client.note_writes[0]["await_process"] is True
    assert len(client.edge_writes) == 1
    assignment = client.edge_writes[0]
    assert assignment.head == client.current.id
    assert assignment.tail == "~Eligible1"
    assert assignment.label == "Resubmission continuity"


def test_existing_current_assignment_prevents_a_second_continuity_assignment():
    client = FakeClient(previous=True)
    client.base_members = {"~Eligible1"}
    client.prior_edges = [prior_edge(client, "~Eligible1", 20)]
    client.current_edges = [SimpleNamespace(tail="~AlreadyAssigned1")]

    run(client)

    assert len(client.note_writes) == 1
    assert client.edge_writes == []
