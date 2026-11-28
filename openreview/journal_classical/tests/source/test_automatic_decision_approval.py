from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SITE_CONFIG = ROOT / "site_config"
PROCESS = SITE_CONFIG / "python_scripts/invitations/venue/decision/process.py"
GUIDANCE = SITE_CONFIG / "python_scripts/invitations/venue/decision/camera_ready_guidance.py"
FIELDS = SITE_CONFIG / "python_scripts/invitations/venue/camera_ready_template_fields.py"
APPROVAL_HELPER = SITE_CONFIG / "python_scripts/invitations/venue/automatic_eic_approval.py"
ADAPTER = SITE_CONFIG / "invitations/venue/decision/invitation/invitation.json"
APPROVAL_VALUE = "I approve the AE's decision."


class FakeOpenReviewException(Exception):
    pass


class FakeNote(SimpleNamespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class FakeJournal:
    venue_id = "JMLR"
    short_name = "JMLR"

    def get_decision_approval_id(self, *, number):
        return f"JMLR/Paper{number}/-/Decision_Approval"

    def get_editors_in_chief_id(self):
        return "JMLR/Editors_In_Chief"

    def get_action_editors_id(self, *, number, anon=False):
        suffix = "Action_Editor_" if anon else "Action_Editors"
        return f"JMLR/Paper{number}/{suffix}"

    def get_camera_ready_revision_id(self, *, number):
        return f"JMLR/Paper{number}/-/Camera_Ready_Revision"

    def get_website_url(self, _key):
        return "https://www.jmlr.org/author-info.html"

    def get_meta_invitation_id(self):
        return "JMLR/-/Edit"


class FakeClient:
    def __init__(
        self,
        *,
        decision_signature="JMLR/Paper7/Action_Editor_1",
        recommendation="Accept as is",
        existing_approvals=(),
        create_approval=True,
        approval_failure=None,
    ):
        self.events = []
        self.decision = SimpleNamespace(
            id="decision-1",
            forum="submission-1",
            signatures=[decision_signature],
            content={"recommendation": {"value": recommendation}},
        )
        self.submission = SimpleNamespace(id="submission-1", number=7)
        self.submission.content = {}
        self.submission.cdate = self.submission.tcdate = 1786838400000
        self.decision.cdate = self.decision.tcdate = 1786838400000
        self.approvals = list(existing_approvals)
        self.create_approval = create_approval
        self.approval_failure = approval_failure
        self.posted = []
        self.invitation_posts = []
        self.get_notes_calls = 0
        self.camera_invitation = SimpleNamespace(
            id="JMLR/Paper7/-/Camera_Ready_Revision",
            edit={
                "note": {
                    "content": {
                        "pdf": {"description": "Base camera-ready description"},
                        "track_id": {"value": "Regular"},
                    }
                }
            },
        )

    def get_note(self, note_id):
        self.events.append(f"get_note:{note_id}")
        return {
            self.decision.id: self.decision,
            self.submission.id: self.submission,
        }[note_id]

    def get_notes(self, *, forum, invitation):
        assert forum == self.submission.id
        assert invitation == "JMLR/Paper7/-/Decision_Approval"
        self.get_notes_calls += 1
        self.events.append("approval_readback")
        return list(self.approvals)

    def post_note_edit(self, **kwargs):
        self.events.append("post_approval")
        self.posted.append(kwargs)
        if self.approval_failure:
            raise self.approval_failure
        if self.create_approval:
            self.approvals.append(SimpleNamespace(
                forum=kwargs["note"].forum,
                replyto=kwargs["note"].replyto,
                signatures=kwargs["signatures"],
                invitations=[kwargs["invitation"]],
                content=kwargs["note"].content,
            ))
        return SimpleNamespace(id="approval-edit-1")

    def post_invitation_edit(self, **_kwargs):
        self.events.append("post_camera_guidance")
        self.invitation_posts.append(_kwargs)

    def get_invitation(self, invitation_id):
        assert invitation_id == self.camera_invitation.id
        self.events.append("camera_guidance_readback")
        return self.camera_invitation

    def post_message(self, **_kwargs):
        raise AssertionError("the adapter must not synthesize notifications")


def load_adapter(monkeypatch, *, enabled=True, native_failure=None):
    journal = FakeJournal()
    original_constructor = lambda: "original-journal"

    openreview_module = ModuleType("openreview")
    openreview_module.api = SimpleNamespace(Note=FakeNote)
    openreview_module.OpenReviewException = FakeOpenReviewException

    journal_module = ModuleType("openreview.journal")
    journal_module.Journal = original_constructor
    journal_module.JournalRequest = SimpleNamespace(
        get_journal=lambda client, journal_id: journal
    )
    openreview_module.journal = journal_module

    process_package = ModuleType("openreview.journal.process")
    native_module = ModuleType("openreview.journal.process.submission_decision_process")

    def native_process(client, edit, invitation):
        client.events.append("native_decision")
        assert journal_module.Journal() is journal
        if native_failure:
            raise native_failure

    native_module.process = native_process
    process_package.submission_decision_process = native_module
    monkeypatch.setitem(sys.modules, "openreview", openreview_module)
    monkeypatch.setitem(sys.modules, "openreview.journal", journal_module)
    monkeypatch.setitem(sys.modules, "openreview.journal.process", process_package)
    monkeypatch.setitem(
        sys.modules,
        "openreview.journal.process.submission_decision_process",
        native_module,
    )

    fields_source = FIELDS.read_text(encoding="utf-8")
    guidance_source = GUIDANCE.read_text(encoding="utf-8").replace(
        '"{{PYTHON_SCRIPT_JSON:invitations/venue/camera_ready_template_fields.py}}"',
        json.dumps(fields_source),
    )
    source = PROCESS.read_text(encoding="utf-8").replace(
        '"{{PYTHON_SCRIPT_JSON:invitations/venue/decision/camera_ready_guidance.py}}"',
        json.dumps(guidance_source),
    )
    source = source.replace(
        '"{{PYTHON_SCRIPT_JSON:invitations/venue/automatic_eic_approval.py}}"',
        json.dumps(APPROVAL_HELPER.read_text(encoding="utf-8")),
    )
    source = source.replace("{{PROD_JOURNAL_ID}}", "journal-request-note")
    source = source.replace(
        "{{AUTOMATIC_DECISION_APPROVAL_JSON}}", "true" if enabled else "false"
    )
    namespace = {"openreview": openreview_module}
    exec(compile(source, str(PROCESS), "exec"), namespace)
    return namespace["process"], journal, journal_module, original_constructor


def invoke(process, client):
    edit = SimpleNamespace(
        id="decision-edit-1",
        signatures=list(client.decision.signatures),
        note=SimpleNamespace(id=client.decision.id),
    )
    process(client, edit, SimpleNamespace(id="JMLR/Paper7/-/Decision"))


def test_enabled_ae_decision_runs_native_once_before_one_standard_approval(monkeypatch):
    process, _journal, journal_module, original_constructor = load_adapter(monkeypatch)
    client = FakeClient()

    invoke(process, client)

    assert client.events.count("native_decision") == 1
    assert client.events.index("native_decision") < client.events.index("post_approval")
    assert len(client.posted) == 1
    assert len(client.invitation_posts) == 1
    assert client.events.index("post_approval") < client.events.index("post_camera_guidance")
    assert journal_module.Journal is original_constructor


def test_disabled_policy_stops_after_native_decision(monkeypatch):
    process, _journal, _module, _original = load_adapter(monkeypatch, enabled=False)
    client = FakeClient()

    invoke(process, client)

    assert client.events == ["native_decision"]
    assert client.posted == []
    assert client.invitation_posts == []


def test_native_decision_failure_posts_no_approval_and_restores_constructor(monkeypatch):
    failure = RuntimeError("native failed")
    process, _journal, journal_module, original_constructor = load_adapter(
        monkeypatch, native_failure=failure
    )
    client = FakeClient()

    with pytest.raises(RuntimeError, match="native failed"):
        invoke(process, client)

    assert client.posted == []
    assert client.invitation_posts == []
    assert journal_module.Journal is original_constructor


def test_only_ae_signed_submitted_decision_enters_automatic_approval(monkeypatch):
    process, _journal, _module, _original = load_adapter(monkeypatch)
    ae_client = FakeClient(decision_signature="JMLR/Paper7/Action_Editor_9")
    eic_client = FakeClient(decision_signature="JMLR/Editors_In_Chief")

    invoke(process, ae_client)
    invoke(process, eic_client)

    assert len(ae_client.posted) == 1
    assert len(ae_client.invitation_posts) == 1
    assert eic_client.events == [
        "native_decision",
        "get_note:decision-1",
        "get_note:submission-1",
    ]
    assert eic_client.posted == []
    assert eic_client.invitation_posts == []


@pytest.mark.parametrize(
    "recommendation",
    ("Reject", "Reject with encouragement to resubmit"),
)
def test_rejection_is_automatically_approved_without_camera_ready_guidance(
    monkeypatch, recommendation
):
    process, _journal, _module, _original = load_adapter(monkeypatch)
    client = FakeClient(recommendation=recommendation)

    invoke(process, client)

    assert len(client.posted) == 1
    assert client.invitation_posts == []
    assert "post_camera_guidance" not in client.events


@pytest.mark.parametrize(
    "recommendation",
    ("Accept as is", "Accept with minor revision"),
)
def test_acceptance_runs_camera_ready_guidance_once(monkeypatch, recommendation):
    process, _journal, _module, _original = load_adapter(monkeypatch)
    client = FakeClient(recommendation=recommendation)

    invoke(process, client)

    assert len(client.posted) == 1
    assert client.events.count("post_camera_guidance") == 1
    assert len(client.invitation_posts) == 1


@pytest.mark.parametrize("same_decision", (True, False))
def test_idempotence_is_scoped_to_the_same_decision(monkeypatch, same_decision):
    process, _journal, _module, _original = load_adapter(monkeypatch)
    existing = SimpleNamespace(
        forum="submission-1",
        replyto="decision-1" if same_decision else "decision-older",
        signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Decision_Approval"],
        content={
            "approval": {"value": APPROVAL_VALUE},
            "comment_to_the_AE": {"value": (
                "Automatically approved per JMLR policy. This approval uses the "
                "standard Journal decision-approval value."
            )},
        },
    )
    client = FakeClient(existing_approvals=[existing])

    invoke(process, client)

    assert len(client.posted) == (0 if same_decision else 1)
    assert len(client.invitation_posts) == 1


def test_approval_uses_native_checked_value_eic_signature_and_awaited_readback(monkeypatch):
    process, _journal, _module, _original = load_adapter(monkeypatch)
    client = FakeClient()

    invoke(process, client)

    posted = client.posted[0]
    assert posted["invitation"] == "JMLR/Paper7/-/Decision_Approval"
    assert posted["signatures"] == ["JMLR/Editors_In_Chief"]
    assert posted["await_process"] is True
    assert posted["note"].forum == "submission-1"
    assert posted["note"].replyto == "decision-1"
    assert posted["note"].content["approval"]["value"] == APPROVAL_VALUE
    assert client.get_notes_calls == 2
    assert client.events[-1] == "camera_guidance_readback"


def test_missing_approval_readback_fails_without_synthesizing_state(monkeypatch):
    process, _journal, _module, _original = load_adapter(monkeypatch)
    client = FakeClient(create_approval=False)

    with pytest.raises(FakeOpenReviewException, match="readback failed"):
        invoke(process, client)

    assert len(client.posted) == 1
    assert client.approvals == []


def test_approval_post_failure_propagates_without_synthesizing_state(monkeypatch):
    process, _journal, _module, _original = load_adapter(monkeypatch)
    client = FakeClient(approval_failure=RuntimeError("approval failed"))

    with pytest.raises(RuntimeError, match="approval failed"):
        invoke(process, client)

    assert client.approvals == []
    assert client.events[-1] == "post_approval"


def test_adapter_surface_owns_only_auto_approval_and_camera_guidance():
    overlay = json.loads(ADAPTER.read_text(encoding="utf-8"))
    source = PROCESS.read_text(encoding="utf-8")

    assert overlay["content"] == {
        "process_script": {
            "value": "{{PYTHON_SCRIPT_JSON:invitations/venue/decision/process.py}}"
        }
    }
    assert overlay["postprocesses"] == []
    signature_items = overlay["edit"]["invitation"]["edit"]["signatures"]["param"]["items"]
    assert signature_items == [
        {"value": "JMLR/Editors_In_Chief", "optional": True},
        {
            "prefix": "JMLR/Paper${7/content/noteNumber/value}/Action_Editor_",
            "optional": True,
        },
    ]
    assert "decision/camera_ready_guidance.py" in source
    assert "automatic_eic_approval.py" in source
    assert source.index("submission_decision_process.process") < source.index(
        "post_standard_eic_approval"
    )
    approval_overlay = json.loads(
        (SITE_CONFIG / "invitations/venue/decision_approval/invitation/invitation.json").read_text()
    )
    assert approval_overlay["postprocesses"] == []
    approval_postprocesses = approval_overlay["edit"]["invitation"]["postprocesses"]
    assert len(approval_postprocesses) == 1
    assert "decision_approval/postprocess.py" in approval_postprocesses[0]["script"]
    for forbidden in (
        "release",
        "reject",
        "rejected",
        "post_message",
        "post_edge",
        "post_group_edit",
        "set_note_",
        "expire_task",
        "task",
        "dateprocesses",
        "notify",
        "notification",
    ):
        assert forbidden not in source


def test_jmlr_auto_approval_is_an_explicit_enabled_setting():
    settings = json.loads((SITE_CONFIG / "openreview.json").read_text(encoding="utf-8"))

    assert settings["defaults"]["request_form"]["automatic_decision_approval"] is True


def test_rejected_callback_creates_before_it_replaces_resubmission_invitation():
    process = (
        SITE_CONFIG / "invitations/venue/rejected/process_functions/process.py"
    ).read_text(encoding="utf-8")

    assert "existing_resubmission = openreview.tools.get_invitation(" in process
    assert "replacement=bool(existing_resubmission)" in process
    assert "await_process=True" in process
    assert "created_resubmission = client.get_invitation(resubmission_id)" in process
    assert "Resubmission invitation readback failed." in process
