from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site_config"
SOURCE = SITE / "python_scripts/invitations/venue/decision_approval/postprocess.py"
GUIDANCE = SITE / "python_scripts/invitations/venue/decision/camera_ready_guidance.py"
FIELDS = SITE / "python_scripts/invitations/venue/camera_ready_template_fields.py"
OVERLAY = SITE / "invitations/venue/decision_approval/invitation/invitation.json"


class Journal:
    venue_id = "JMLR"
    short_name = "JMLR"

    def get_camera_ready_revision_id(self, *, number):
        return f"JMLR/Paper{number}/-/Camera_Ready_Revision"

    def get_website_url(self, _key):
        return "https://www.jmlr.org/author-info.html"

    def get_meta_invitation_id(self):
        return "JMLR/-/Edit"


class Client:
    def __init__(self, *, approval="I approve the AE's decision.", recommendation="Accept as is", updated=False):
        self.approval = SimpleNamespace(
            id="approval", replyto="decision", tcdate=1, tmdate=2 if updated else 1,
            content={"approval": {"value": approval}},
        )
        self.decision = SimpleNamespace(
            id="decision", forum="forum", tcdate=1786838400000,
            content={"recommendation": {"value": recommendation}},
        )
        self.submission = SimpleNamespace(
            id="forum", number=7, tcdate=1784246400000,
            content={
                "title": {"value": "Paper"},
                "authors": {"value": ["Author"]},
                "authorids": {"value": ["~Author1"]},
            },
        )
        self.camera = SimpleNamespace(
            id="JMLR/Paper7/-/Camera_Ready_Revision",
            edit={"note": {"content": {
                "pdf": {"description": "Base camera-ready description"},
                "track_id": {"value": "Regular"},
            }}},
        )
        self.posts = []

    def get_note(self, note_id):
        return {
            "approval": self.approval,
            "decision": self.decision,
            "forum": self.submission,
        }[note_id]

    def get_invitation(self, invitation_id):
        assert invitation_id == self.camera.id
        return self.camera

    def post_invitation_edit(self, **kwargs):
        self.posts.append(kwargs)


def load_process():
    fields = FIELDS.read_text(encoding="utf-8")
    guidance = GUIDANCE.read_text(encoding="utf-8").replace(
        '"{{PYTHON_SCRIPT_JSON:invitations/venue/camera_ready_template_fields.py}}"',
        json.dumps(fields),
    )
    source = SOURCE.read_text(encoding="utf-8").replace(
        '"{{PYTHON_SCRIPT_JSON:invitations/venue/decision/camera_ready_guidance.py}}"',
        json.dumps(guidance),
    ).replace("{{PROD_JOURNAL_ID}}", "request")
    journal = Journal()
    openreview = SimpleNamespace(
        journal=SimpleNamespace(JournalRequest=SimpleNamespace(
            get_journal=lambda _client, request_id: journal if request_id == "request" else None,
        )),
        OpenReviewException=RuntimeError,
    )
    namespace = {"openreview": openreview}
    exec(compile(source, str(SOURCE), "exec"), namespace)
    return namespace["process"]


def invoke(client):
    load_process()(
        client,
        SimpleNamespace(note=SimpleNamespace(id="approval")),
        SimpleNamespace(id="JMLR/Paper7/-/Decision_Approval"),
    )


@pytest.mark.parametrize("recommendation", ("Accept as is", "Accept with minor revision"))
def test_manual_acceptance_applies_jmlr_guidance_once(recommendation):
    client = Client(recommendation=recommendation)

    invoke(client)
    invoke(client)

    assert len(client.posts) == 1
    content = client.camera.edit["note"]["content"]
    assert "track_id" not in content
    assert "JMLR LaTeX metadata" in content["pdf"]["description"]
    assert "Official JMLR Author Guidelines" in content["pdf"]["description"]


@pytest.mark.parametrize(
    "client",
    (
        Client(approval="I don't approve the AE's decision. The AE needs to revise their decision."),
        Client(recommendation="Reject"),
        Client(updated=True),
    ),
)
def test_decline_rejection_and_updated_approval_do_not_touch_camera_guidance(client):
    invoke(client)

    assert client.posts == []
    assert "track_id" in client.camera.edit["note"]["content"]


def test_generated_paper_scoped_approval_invitation_owns_the_callback():
    overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))

    assert overlay["postprocesses"] == []
    postprocesses = overlay["edit"]["invitation"]["postprocesses"]
    assert len(postprocesses) == 1
    assert "decision_approval/postprocess.py" in postprocesses[0]["script"]
