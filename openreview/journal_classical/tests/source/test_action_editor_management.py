"""Characterize the approved JMLR Action Editor management surface."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site_config"
MANAGE = SITE / "invitations/venue/manage_action_editors"
ADD = SITE / "invitations/venue/add_action_editor"
ROLE = SITE / "invitations/venue/role_management"


def load_process(path: Path, openreview):
    namespace = {"openreview": openreview}
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
    return namespace["process"]


def journal_openreview(journal):
    return SimpleNamespace(
        OpenReviewException=RuntimeError,
        journal=SimpleNamespace(
            JournalRequest=SimpleNamespace(get_journal=lambda _client, _id: journal)
        ),
    )


def test_invitation_schemas_separate_add_and_guarded_remove():
    add_invitation = json.loads((ADD / "invitation/invitation.json").read_text())
    add_reply = json.loads((ADD / "edit/reply.json").read_text())
    manage_invitation = json.loads((MANAGE / "invitation/invitation.json").read_text())
    manage_reply = json.loads((MANAGE / "edit/reply.json").read_text())

    assert add_invitation["id"] == "JMLR/-/Add_Action_Editor"
    assert add_reply["group"]["members"]["param"]["change"] == "add"
    assert manage_invitation["id"] == "JMLR/-/Manage_Action_Editors"
    assert manage_reply["group"]["members"]["param"]["change"] == "remove"
    for invitation in (add_invitation, manage_invitation):
        assert invitation["invitees"] == ["JMLR/Editors_In_Chief"]
        assert invitation["readers"] == ["JMLR/Editors_In_Chief"]


def test_management_ui_preserves_approved_controls_and_journal_links():
    source = (MANAGE / "web/web.js").read_text(encoding="utf-8")

    assert "Add AE" in source
    assert "jmlr-ae-add-button" in source
    assert "JMLR/-/Add_Action_Editor" in source
    assert "JMLR/-/Manage_Action_Editors" in source
    assert "data-track=\"Regular\"" in source
    assert "JMLR/Action_Editors/-/Track_Eligible" in source
    assert 'href="/group?id=JMLR/Action_Editors"' in source
    assert "Manage Tracks" in source
    assert "Assignment_Availability" not in source


def test_role_navigation_preserves_all_approved_destinations():
    invitation = json.loads((ROLE / "invitation/invitation.json").read_text())
    source = (ROLE / "web/web.js").read_text(encoding="utf-8")

    assert invitation["id"] == "JMLR/-/Role_Management"
    for label in (
        "Manage Action Editors",
        "Manage Tracks",
        "Manage AE Availability",
        "Edit Editors-in-Chief",
        "Edit Reviewers",
        "Edit Production Editors",
        "Recruit Action Editors or Reviewers",
        "Venue membership lookup",
    ):
        assert label in source


def test_removal_is_blocked_while_editor_has_an_active_paper():
    journal = SimpleNamespace(
        get_ae_assignment_id=lambda: "JMLR/Action_Editors/-/Assignment",
        is_active_submission=lambda _note: True,
    )
    process = load_process(
        MANAGE / "process_functions/preprocess.py", journal_openreview(journal)
    )
    client = SimpleNamespace(
        get_edges=lambda **_kwargs: [SimpleNamespace(head="paper")],
        get_note=lambda _id: SimpleNamespace(number=7),
    )
    edit = SimpleNamespace(group=SimpleNamespace(members={"remove": ["~Editor1"]}))

    with pytest.raises(RuntimeError, match="Paper7"):
        process(client, edit, SimpleNamespace())


def test_removal_is_allowed_after_active_papers_are_reassigned():
    journal = SimpleNamespace(
        get_ae_assignment_id=lambda: "JMLR/Action_Editors/-/Assignment",
        is_active_submission=lambda _note: False,
    )
    process = load_process(
        MANAGE / "process_functions/preprocess.py", journal_openreview(journal)
    )
    client = SimpleNamespace(
        get_edges=lambda **_kwargs: [SimpleNamespace(head="paper")],
        get_note=lambda _id: SimpleNamespace(number=7),
    )
    edit = SimpleNamespace(group=SimpleNamespace(members={"remove": ["~Editor1"]}))

    process(client, edit, SimpleNamespace())


def test_removal_expires_only_active_jmlr_eligibility_and_is_idempotent():
    regular = SimpleNamespace(
        id="regular", ddate=None, label="Regular Ineligible"
    )
    managed = SimpleNamespace(id="managed", ddate=None, label="OSS")
    expired = SimpleNamespace(id="expired", ddate=10, label="Award")
    by_invitation = {
        "JMLR/Action_Editors/-/Regular_Ineligible": [regular],
        "JMLR/Action_Editors/-/Track_Eligible": [managed, expired],
    }
    posted = []

    def edge(**values):
        return SimpleNamespace(**values)

    def post_edge(replacement):
        posted.append(replacement)
        for original in (regular, managed, expired):
            if original.id == replacement.id:
                original.ddate = replacement.ddate

    openreview = SimpleNamespace(
        api=SimpleNamespace(Edge=edge),
        tools=SimpleNamespace(datetime_millis=lambda _now: 1234),
    )
    process = load_process(MANAGE / "process_functions/process.py", openreview)
    client = SimpleNamespace(
        get_edges=lambda invitation, **_kwargs: by_invitation[invitation],
        post_edge=post_edge,
    )
    edit = SimpleNamespace(group=SimpleNamespace(members={"remove": ["~Editor1"]}))

    process(client, edit, SimpleNamespace())
    process(client, edit, SimpleNamespace())

    assert [(item.id, item.ddate) for item in posted] == [
        ("regular", 1234),
        ("managed", 1234),
    ]
    assert all(item.readers == ["JMLR/Editors_In_Chief", "~Editor1"] for item in posted)
    assert all("Assignment_Availability" not in item.invitation for item in posted)
