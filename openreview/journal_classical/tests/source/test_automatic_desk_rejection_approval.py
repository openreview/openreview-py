from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SITE_CONFIG = ROOT / "site_config"
PROCESS = SITE_CONFIG / "python_scripts/invitations/venue/review_approval/process.py"
HELPER = SITE_CONFIG / "python_scripts/invitations/venue/automatic_eic_approval.py"
ADAPTER = SITE_CONFIG / "invitations/venue/review_approval/invitation/invitation.json"
APPROVAL = "I approve the AE's decision."


class FakeOpenReviewException(Exception):
    pass


class FakeJournal:
    desk_rejected_venue_id = "JMLR/Desk_Rejected"
    under_review_venue_id = "JMLR/Under_Review"
    short_name = "JMLR"

    def __init__(self):
        self.expire_calls = []
        self.invitation_builder = SimpleNamespace(
            expire_paper_invitations=lambda submission: self.expire_calls.append(submission.id)
        )

    def get_action_editors_id(self, *, number, anon=False):
        return f"JMLR/Paper{number}/Action_Editor_" if anon else f"JMLR/Paper{number}/Action_Editors"

    def get_desk_rejection_approval_id(self, *, number):
        return f"JMLR/Paper{number}/-/Desk_Rejection_Approval"

    def get_editors_in_chief_id(self):
        return "JMLR/Editors_In_Chief"

    def get_authors_id(self, number=None):
        return f"JMLR/Paper{number}/Authors" if number else "JMLR/Authors"

    def get_review_approval_id(self, number=None):
        return f"JMLR/Paper{number}/-/Review_Approval"

    def get_reviewer_assignment_id(self, number=None):
        return f"JMLR/Paper{number}/Reviewers/-/Assignment"


class FakeClient:
    def __init__(self, *, signature="JMLR/Paper7/Action_Editor_1", selection="Desk Reject", existing=(), invitation_error=None, persist=True):
        self.events = []
        self.review_approval = SimpleNamespace(
            id="review-approval-7", forum="forum-7", signatures=[signature],
            readers=["JMLR/Editors_In_Chief", "JMLR/Paper7/Action_Editors"],
            content={"under_review": {"value": selection}},
        )
        self.submission = SimpleNamespace(
            id="forum-7", number=7,
            content={
                "venueid": {"value": "JMLR/Submitted"},
                "title": {"value": "Desk fixture"},
            },
        )
        self.approvals = list(existing)
        self.continued = []
        self.invitation_error = invitation_error
        self.persist = persist
        self.posts = []
        self.messages = []

    def get_note(self, note_id):
        self.events.append(f"get_note:{note_id}")
        notes = {"review-approval-7": self.review_approval, "forum-7": self.submission}
        notes.update({note.id: note for note in self.continued})
        return notes[note_id]

    def get_invitation(self, invitation_id):
        if invitation_id == "JMLR/Paper7/Reviewers/-/Assignment":
            self.events.append("reviewer_assignment_readback")
            if self.submission.content["venueid"]["value"] != "JMLR/Under_Review":
                raise FakeOpenReviewException("reviewer assignment missing")
            return SimpleNamespace(id=invitation_id)
        self.events.append("native_invitation_readback")
        assert invitation_id == "JMLR/Paper7/-/Desk_Rejection_Approval"
        if self.invitation_error:
            raise self.invitation_error
        return SimpleNamespace(id=invitation_id)

    def get_notes(self, *, forum, invitation):
        assert forum == "forum-7"
        if invitation == "JMLR/Paper7/-/Review_Approval":
            return list(self.continued)
        assert invitation == "JMLR/Paper7/-/Desk_Rejection_Approval"
        self.events.append("approval_readback")
        return list(self.approvals)

    def post_note_edit(self, **kwargs):
        self.events.append("post_approval")
        self.posts.append(kwargs)
        if self.persist:
            approval = kwargs["note"].content["approval"]["value"]
            self.approvals.append(SimpleNamespace(
                forum=kwargs["note"].forum,
                replyto=kwargs["note"].replyto,
                signatures=kwargs["signatures"],
                invitations=[kwargs["invitation"]],
                content=kwargs["note"].content,
            ))
            if approval == APPROVAL:
                self.submission.content["venueid"]["value"] = "JMLR/Desk_Rejected"
                self.review_approval.readers.append("JMLR/Paper7/Authors")
                self.messages.append({"subject": "decision"})
            else:
                self.continued.append(SimpleNamespace(
                    id="continued-7", forum="forum-7",
                    content={"under_review": {"value": "Appropriate for Review"}}
                ))

    def get_messages(self, *, subject):
        assert subject == "[JMLR] Decision for your JMLR submission 7: Desk fixture"
        return list(self.messages)


def load_adapter(monkeypatch, *, enabled=True, native_failure=None):
    journal = FakeJournal()
    original_constructor = lambda: "original"
    openreview = ModuleType("openreview")
    openreview.api = SimpleNamespace(Note=lambda **kwargs: SimpleNamespace(**kwargs))
    openreview.OpenReviewException = FakeOpenReviewException
    journal_module = ModuleType("openreview.journal")
    journal_module.Journal = original_constructor
    journal_module.JournalRequest = SimpleNamespace(get_journal=lambda _client, _id: journal)
    openreview.journal = journal_module
    package = ModuleType("openreview.journal.process")
    native = ModuleType("openreview.journal.process.review_approval_process")
    desk_native = ModuleType("openreview.journal.process.desk_rejection_approval_process")

    def native_process(client, edit, _invitation):
        selection = edit.note.content["under_review"]["value"]
        if type(edit).__name__ == "ReviewApprovalContinuationRetry":
            assert selection == "Appropriate for Review"
            client.events.append("native_review_approval_continuation_retry")
            client.submission.content["venueid"]["value"] = "JMLR/Under_Review"
            return
        client.events.append("native_review_approval")
        assert journal_module.Journal() is journal
        if native_failure:
            raise native_failure

    native.process = native_process
    package.review_approval_process = native

    def desk_native_process(client, edit, _invitation):
        client.events.append("native_desk_rejection_approval_retry")
        approval = edit.note.content["approval"]["value"]
        if approval == APPROVAL:
            client.submission.content["venueid"]["value"] = "JMLR/Desk_Rejected"
            if "JMLR/Paper7/Authors" not in client.review_approval.readers:
                client.review_approval.readers.append("JMLR/Paper7/Authors")
            if not client.messages:
                client.messages.append({"subject": "decision"})
        else:
            client.continued.append(SimpleNamespace(
                id="continued-7", forum="forum-7",
                content={"under_review": {"value": "Appropriate for Review"}}
            ))

    desk_native.process = desk_native_process
    package.desk_rejection_approval_process = desk_native
    for name, module in (
        ("openreview", openreview),
        ("openreview.journal", journal_module),
        ("openreview.journal.process", package),
        ("openreview.journal.process.review_approval_process", native),
        ("openreview.journal.process.desk_rejection_approval_process", desk_native),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    source = PROCESS.read_text(encoding="utf-8")
    source = source.replace(
        '"{{PYTHON_SCRIPT_JSON:invitations/venue/automatic_eic_approval.py}}"',
        json.dumps(HELPER.read_text(encoding="utf-8")),
    )
    source = source.replace("{{PROD_JOURNAL_ID}}", "journal-request")
    source = source.replace(
        "{{AUTOMATIC_DESK_REJECTION_APPROVAL_JSON}}", "true" if enabled else "false"
    )
    namespace = {"openreview": openreview}
    exec(compile(source, str(PROCESS), "exec"), namespace)
    return namespace["process"], journal_module, original_constructor


def invoke(process, client):
    process(client, SimpleNamespace(note=client.review_approval), SimpleNamespace())


def test_enabled_ae_desk_reject_runs_native_before_exact_standard_approval(monkeypatch):
    process, module, original = load_adapter(monkeypatch)
    client = FakeClient()

    invoke(process, client)

    assert client.events.index("native_review_approval") < client.events.index("native_invitation_readback") < client.events.index("post_approval")
    post = client.posts[0]
    assert post["invitation"] == "JMLR/Paper7/-/Desk_Rejection_Approval"
    assert post["signatures"] == ["JMLR/Editors_In_Chief"]
    assert post["await_process"] is True
    assert post["note"].content["approval"]["value"] == APPROVAL
    assert post["note"].content["comment"]["value"]
    assert module.Journal is original


def test_disabled_policy_preserves_native_pending_task_without_approval(monkeypatch):
    process, _module, _original = load_adapter(monkeypatch, enabled=False)
    client = FakeClient()

    invoke(process, client)

    assert client.events == ["native_review_approval"]
    assert client.posts == []


@pytest.mark.parametrize("selection", ["Appropriate for Review"])
def test_non_desk_selection_never_enters_automatic_approval(monkeypatch, selection):
    process, _module, _original = load_adapter(monkeypatch)
    client = FakeClient(selection=selection)

    invoke(process, client)

    assert client.events == ["native_review_approval", "get_note:review-approval-7"]
    assert client.posts == []


def test_non_ae_signature_never_enters_automatic_approval(monkeypatch):
    process, _module, _original = load_adapter(monkeypatch)
    client = FakeClient(signature="JMLR/Editors_In_Chief")

    invoke(process, client)

    assert "native_review_approval" in client.events
    assert "native_invitation_readback" not in client.events
    assert client.posts == []


def test_native_failure_posts_nothing_and_restores_journal_constructor(monkeypatch):
    process, module, original = load_adapter(monkeypatch, native_failure=RuntimeError("native failed"))
    client = FakeClient()

    with pytest.raises(RuntimeError, match="native failed"):
        invoke(process, client)

    assert client.posts == []
    assert module.Journal is original


def test_missing_native_invitation_never_synthesizes_approval(monkeypatch):
    process, _module, _original = load_adapter(monkeypatch)
    client = FakeClient(invitation_error=RuntimeError("native invitation failed"))

    with pytest.raises(RuntimeError, match="native invitation failed"):
        invoke(process, client)
    assert client.posts == []


def test_retry_is_idempotent_for_same_review_approval(monkeypatch):
    process, _module, _original = load_adapter(monkeypatch)
    client = FakeClient(existing=[SimpleNamespace(
        forum="forum-7", replyto="review-approval-7",
        signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Desk_Rejection_Approval"],
        content={"approval": {"value": APPROVAL},
                 "comment": {"value": "Automatically approved per JMLR desk-rejection policy."}},
    )])
    client.submission.content["venueid"]["value"] = "JMLR/Desk_Rejected"
    client.review_approval.readers.append("JMLR/Paper7/Authors")
    client.messages.append({"subject": "decision"})

    invoke(process, client)

    assert client.events[0] == "native_review_approval"
    assert client.posts == []
    assert "native_desk_rejection_approval_retry" not in client.events
    assert len(client.messages) == 1


def test_duplicate_author_notification_is_rejected_without_reprocessing(monkeypatch):
    process, _module, _original = load_adapter(monkeypatch)
    existing = SimpleNamespace(
        forum="forum-7", replyto="review-approval-7",
        signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Desk_Rejection_Approval"],
        content={"approval": {"value": APPROVAL},
                 "comment": {"value": "Automatically approved per JMLR desk-rejection policy."}},
    )
    client = FakeClient(existing=[existing])
    client.submission.content["venueid"]["value"] = "JMLR/Desk_Rejected"
    client.review_approval.readers.append("JMLR/Paper7/Authors")
    client.messages.extend([{"subject": "decision"}, {"subject": "decision"}])

    with pytest.raises(FakeOpenReviewException, match="notification duplicated"):
        invoke(process, client)
    assert "native_desk_rejection_approval_retry" not in client.events


def test_existing_manual_decline_is_authoritative_and_requires_continued_state(monkeypatch):
    process, _module, _original = load_adapter(monkeypatch)
    decline = "I don't approve the AE's decision. Submission should be appropriate for review."
    existing = SimpleNamespace(
        forum="forum-7", replyto="review-approval-7",
        signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Desk_Rejection_Approval"],
        content={"approval": {"value": decline}, "comment": {"value": "Manual review."}},
    )
    client = FakeClient(existing=[existing])
    client.continued.append(SimpleNamespace(
        id="continued-7", forum="forum-7",
        content={"under_review": {"value": "Appropriate for Review"}}
    ))
    client.submission.content["venueid"]["value"] = "JMLR/Under_Review"

    invoke(process, client)

    assert client.posts == []
    assert client.submission.content["venueid"]["value"] == "JMLR/Under_Review"
    assert "native_desk_rejection_approval_retry" not in client.events
    assert "native_review_approval_continuation_retry" not in client.events


def test_existing_decline_continuation_with_unsettled_root_resumes_its_native_process(monkeypatch):
    process, _module, _original = load_adapter(monkeypatch)
    decline = "I don't approve the AE's decision. Submission should be appropriate for review."
    existing = SimpleNamespace(
        forum="forum-7", replyto="review-approval-7",
        signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Desk_Rejection_Approval"],
        content={"approval": {"value": decline},
                 "comment": {"value": "Manual review."}},
    )
    client = FakeClient(existing=[existing])
    client.continued.append(SimpleNamespace(
        id="continued-7", forum="forum-7",
        content={"under_review": {"value": "Appropriate for Review"}},
    ))

    invoke(process, client)

    assert client.posts == []
    assert client.submission.content["venueid"]["value"] == "JMLR/Under_Review"
    assert client.events.count("native_review_approval_continuation_retry") == 1
    assert "native_desk_rejection_approval_retry" not in client.events


def test_note_without_settled_native_outcome_is_safely_resumed(monkeypatch):
    process, _module, _original = load_adapter(monkeypatch)
    existing = SimpleNamespace(
        forum="forum-7", replyto="review-approval-7",
        signatures=["JMLR/Editors_In_Chief"],
        invitations=["JMLR/Paper7/-/Desk_Rejection_Approval"],
        content={"approval": {"value": APPROVAL},
                 "comment": {"value": "Automatically approved per JMLR desk-rejection policy."}},
    )
    client = FakeClient(existing=[existing])

    invoke(process, client)

    assert client.posts == []
    assert client.events.count("native_desk_rejection_approval_retry") == 1
    assert client.submission.content["venueid"]["value"] == "JMLR/Desk_Rejected"
    assert len(client.messages) == 1


def test_missing_approval_readback_fails_after_one_post(monkeypatch):
    process, _module, _original = load_adapter(monkeypatch)
    client = FakeClient(persist=False)

    with pytest.raises(FakeOpenReviewException, match="desk-rejection approval readback failed"):
        invoke(process, client)
    assert len(client.posts) == 1


def test_static_wiring_is_narrow_and_setting_defaults_enabled():
    overlay = json.loads(ADAPTER.read_text(encoding="utf-8"))
    source = PROCESS.read_text(encoding="utf-8")
    settings = json.loads((SITE_CONFIG / "openreview.json").read_text(encoding="utf-8"))

    assert overlay == {
        "content": {"process_script": {"value": "{{PYTHON_SCRIPT_JSON:invitations/venue/review_approval/process.py}}"}},
        "postprocesses": [],
    }
    assert "from openreview.journal.process import review_approval_process" in source
    assert source.index("review_approval_process.process") < source.index("post_standard_eic_approval")
    assert "wait_for_native_invitation(client, approval_id)" in source
    assert "automatic_eic_approval.py" in source
    assert "desk_rejection_approval_process.process" in source
    assert "expire_paper_invitations(submission)" in source
    assert "get_messages(subject=subject)" in source
    assert settings["defaults"]["request_form"]["automatic_desk_rejection_approval"] is True
    for forbidden in ("post_message", "get_desk_rejected_id"):
        assert forbidden not in source
