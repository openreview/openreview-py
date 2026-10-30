import json
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "site_config/python_scripts/invitations/venue/production_change_notification/postprocess.py"
DOC = ROOT / "docs/workflow/actions/retraction.md"


class FakeOpenReviewException(Exception):
    pass


class Client:
    def __init__(self, approval="Yes", venueid="JMLR/Retracted_Acceptance", *, timeout_after_delivery=False, settle_after=0):
        self.approval = SimpleNamespace(
            id="approval-7", forum="forum-7",
            content={"approval": {"value": approval}},
        )
        self.submission = SimpleNamespace(
            id="forum-7", number=7,
            content={"venueid": {"value": venueid}},
        )
        self.messages = []
        self.posts = []
        self.timeout_after_delivery = timeout_after_delivery
        self.settle_after = settle_after
        self.submission_reads = 0

    def get_note(self, note_id):
        if note_id == "forum-7":
            self.submission_reads += 1
            if self.settle_after and self.submission_reads >= self.settle_after:
                self.submission.content["venueid"]["value"] = "JMLR/Retracted_Acceptance"
        return {"approval-7": self.approval, "forum-7": self.submission}[note_id]

    def get_messages(self, *, subject):
        return [
            item for item in self.messages
            if item["content"]["subject"] == subject
        ]

    def post_message(self, **kwargs):
        self.posts.append(kwargs)
        self.messages.append({"id": f"message-{len(self.posts)}", "requestId": f"request-{len(self.posts)}", "content": {
            "subject": kwargs["subject"],
            "text": kwargs["message"],
        }})
        if self.timeout_after_delivery:
            self.timeout_after_delivery = False
            raise TimeoutError("delivery response timed out")


def load_process():
    source = SOURCE.read_text(encoding="utf-8")
    source = source.replace("{{PROD_JOURNAL_ID}}", "request")
    source = source.replace(
        '"{{EMAIL_TEMPLATE_JSON:production_editor/production_change_subject.txt}}"',
        json.dumps("[{short_name}] Production follow-up: {event} for paper {submission_number}"),
    ).replace(
        '"{{EMAIL_TEMPLATE_JSON:production_editor/production_change.txt}}"',
        json.dumps("A {event} was completed for paper {submission_number}: {paper_url}"),
    ).replace("{{SITE_URL}}", "https://dev.openreview.net")
    journal = SimpleNamespace(
        short_name="JMLR", venue_id="JMLR", retracted_venue_id="JMLR/Retracted_Acceptance",
        contact_info="no-reply@jmlr.org",
        get_meta_invitation_id=lambda: "JMLR/-/Edit",
        get_message_sender=lambda: "jmlr-notifications@openreview.net",
    )
    openreview = SimpleNamespace(
        journal=SimpleNamespace(JournalRequest=SimpleNamespace(
            get_journal=lambda _client, _request: journal,
        )),
        OpenReviewException=FakeOpenReviewException,
    )
    namespace = {"openreview": openreview}
    exec(compile(source, str(SOURCE), "exec"), namespace)
    return namespace["process"]


def invoke(
    client,
    *,
    invitation="JMLR/Paper7/-/Retraction_Approval",
    edit_id="edit-retraction-7",
):
    load_process()(
        client,
        SimpleNamespace(id=edit_id, note=SimpleNamespace(id="approval-7")),
        SimpleNamespace(id=invitation),
    )


def test_yes_retraction_notifies_production_editors_once_after_settled_root():
    client = Client()

    invoke(client)
    invoke(client)

    assert len(client.posts) == 1
    post = client.posts[0]
    assert post["recipients"] == ["JMLR/Production_Editors"]
    assert "retraction of an accepted paper" in post["subject"]
    assert "https://dev.openreview.net/forum?id=forum-7" in post["message"]


def test_no_retraction_never_notifies_production_editors():
    client = Client(approval="No", venueid="JMLR")

    invoke(client)

    assert client.posts == [] and client.messages == []


def test_yes_retraction_requires_native_retracted_state(monkeypatch):
    client = Client(venueid="JMLR")
    ticks = iter((0, 31))
    monkeypatch.setattr("time.monotonic", lambda: next(ticks))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    with pytest.raises(FakeOpenReviewException, match="settled retracted record"):
        invoke(client)
    assert client.posts == []


def test_yes_retraction_waits_for_native_root_to_settle(monkeypatch):
    client = Client(venueid="JMLR", settle_after=3)
    ticks = iter((0, 1, 2))
    monkeypatch.setattr("time.monotonic", lambda: next(ticks))
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    invoke(client)

    assert client.submission_reads >= 3
    assert len(client.posts) == 1


def test_timeout_after_delivery_is_idempotent_on_retry():
    client = Client(timeout_after_delivery=True)

    invoke(client)
    invoke(client)

    assert len(client.posts) == 1
    assert len(client.messages) == 1


def test_duplicate_existing_messages_fail_closed():
    client = Client()
    subject = "[JMLR] Production follow-up: retraction of an accepted paper for paper 7"
    message = "OpenReview production-change event: edit-retraction-7"
    client.messages = [
        {"id": "one", "requestId": "request-one", "content": {"subject": subject, "text": message}},
        {"id": "two", "requestId": "request-two", "content": {"subject": subject, "text": message}},
    ]

    with pytest.raises(FakeOpenReviewException, match="Duplicate"):
        invoke(client)
    assert client.posts == []


def test_one_group_delivery_fanned_out_to_two_recipients_is_idempotent():
    client = Client()
    subject = "[JMLR] Production follow-up: retraction of an accepted paper for paper 7"
    message = "OpenReview production-change event: edit-retraction-7"
    client.messages = [
        {"id": "recipient-one", "requestId": "same-request", "content": {"subject": subject, "text": message}},
        {"id": "recipient-two", "requestId": "same-request", "content": {"subject": subject, "text": message}},
    ]

    invoke(client)

    assert client.posts == []


def test_distinct_eic_revisions_each_notify_once_despite_same_paper_subject():
    client = Client(venueid="JMLR")
    invitation = "JMLR/Paper7/-/EIC_Revision"

    invoke(client, invitation=invitation, edit_id="edit-revision-1")
    invoke(client, invitation=invitation, edit_id="edit-revision-1")
    invoke(client, invitation=invitation, edit_id="edit-revision-2")
    invoke(client, invitation=invitation, edit_id="edit-revision-2")

    assert len(client.posts) == 2
    assert len(client.messages) == 2
    bodies = [item["content"]["text"] for item in client.messages]
    assert any("edit-revision-1" in body for body in bodies)
    assert any("edit-revision-2" in body for body in bodies)


def test_missing_event_identity_fails_before_delivery():
    client = Client()

    with pytest.raises(FakeOpenReviewException, match="event identity is missing"):
        invoke(client, edit_id=None)
    assert client.posts == []


def test_retraction_design_and_inventory_match_native_control_and_jmlr_callback():
    design = DOC.read_text(encoding="utf-8")
    inventory = (ROOT / "docs/workflow/action-inventory.md").read_text(encoding="utf-8")
    policies = (ROOT / "docs/workflow/editorial-policies.md").read_text(encoding="utf-8")
    accepted = (ROOT.parent / "journal/process/accepted_submission_process.py").read_text(encoding="utf-8")
    overlay = json.loads((
        ROOT / "site_config/invitations/venue/retraction_approval/invitation/invitation.json"
    ).read_text(encoding="utf-8"))
    assert "set_note_retraction_invitation" in accepted
    assert overlay["postprocesses"] == []
    nested_postprocesses = overlay["edit"]["invitation"]["postprocesses"]
    assert len(nested_postprocesses) == 1
    assert "production_change_notification/postprocess.py" in nested_postprocesses[0]["script"]
    eic_overlay = json.loads((
        ROOT / "site_config/invitations/venue/eic_revision/invitation/invitation.json"
    ).read_text(encoding="utf-8"))
    assert eic_overlay["postprocesses"] == []
    assert eic_overlay["edit"]["invitation"]["postprocesses"] == nested_postprocesses
    for phrase in (
        "`Retraction`", "`Retraction Approval`", "`Yes`", "`No`",
        "immutable historical handoff state", "external jmlr.org",
    ):
        assert phrase in design
    assert "Accepted-paper retraction" in inventory
    assert "Retraction Approval" in policies
    assert "no later publication gate or retraction control" not in policies
