"""JMLR narrows Journal's camera-ready surfaces without forking its lifecycle."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site_config"


def load(relative):
    return json.loads((SITE / relative).read_text(encoding="utf-8"))


def test_author_camera_ready_form_contains_only_pdf_and_supplement():
    payload = load("invitations/venue/camera_ready_revision/edit/reply.json")
    fields = payload["invitation"]["edit"]["note"]["content"]

    assert payload["readers"] == ["JMLR"]
    assert list(fields) == ["pdf", "supplementary_material"]
    assert fields["pdf"]["value"]["param"]["type"] == "file"
    supplement = fields["supplementary_material"]["value"]["param"]
    assert supplement == {
        "type": "file",
        "extensions": ["zip", "pdf"],
        "maxSize": 10,
        "optional": True,
        "deletable": True,
    }
    assert payload["replacement"] is True
    assert "process_script" in payload["invitation"]["process"]
    assert len(payload["invitation"]["dateprocesses"]) == 1
    assert "camera_ready/dateprocess_reminder.py" in payload["invitation"]["dateprocesses"][0]["script"]


def test_camera_ready_material_contract_is_track_agnostic():
    payload = load("invitations/venue/camera_ready_revision/edit/reply.json")
    encoded = json.dumps(payload)

    assert all(track_id not in encoded for track_id in ("Regular", "OSS", "Award"))
    assert payload["invitation"]["edit"]["note"]["content"][
        "supplementary_material"
    ]["value"]["param"]["optional"] is True


def test_ae_verification_is_approval_only_and_directs_corrections_to_comment():
    payload = load("invitations/venue/camera_ready_verification/edit/reply.json")
    fields = payload["invitation"]["edit"]["note"]["content"]

    assert payload["readers"] == ["JMLR"]
    assert list(fields) == ["verification"]
    verification = fields["verification"]
    assert verification["value"]["param"]["input"] == "checkbox"
    assert verification["value"]["param"]["enum"] == [
        "I confirm that the latest camera-ready manuscript satisfies the JMLR camera-ready requirements."
    ]
    assert "Official Comment" in verification["description"]
    assert "do not submit this approval" in verification["description"]
    assert "Request camera-ready revision" not in json.dumps(payload)
    assert "revision_comments" not in json.dumps(payload)
    assert "process_script" in payload["invitation"]["process"]
    assert len(payload["invitation"]["dateprocesses"]) == 1
    assert "camera_ready/dateprocess_reminder.py" in payload["invitation"]["dateprocesses"][0]["script"]


def test_camera_ready_forms_share_one_reminder_owner():
    revision = load("invitations/venue/camera_ready_revision/edit/reply.json")
    verification = load("invitations/venue/camera_ready_verification/edit/reply.json")
    revision_script = revision["invitation"]["dateprocesses"][0]["script"]
    verification_script = verification["invitation"]["dateprocesses"][0]["script"]

    assert revision_script == verification_script
    assert "camera_ready/dateprocess_reminder.py" in revision_script
    assert not (
        SITE / "python_scripts/invitations/venue/camera_ready_revision/dateprocess_reminder.py"
    ).exists()
    assert not (
        SITE / "python_scripts/invitations/venue/camera_ready_verification/dateprocess_reminder.py"
    ).exists()


def test_camera_ready_sources_have_no_separate_final_author_field():
    camera_ready_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (SITE / "invitations/venue").rglob("*")
        if path.is_file() and path.suffix in {".py", ".json", ".js", ".txt"}
    ).lower()
    retired = "final" + "_publication_author_list"
    assert retired not in camera_ready_source


def test_jmlr_schema_reuses_journal_processes_and_adds_only_guidance():
    approval = (
        SITE / "python_scripts/invitations/venue/decision/camera_ready_guidance.py"
    ).read_text(encoding="utf-8")
    revision = (
        SITE / "python_scripts/invitations/venue/camera_ready_revision/postprocess.py"
    ).read_text(encoding="utf-8")

    assert "get_camera_ready_template_fields" in approval
    assert "camera_ready_author_guidelines" in approval
    assert "JMLR LaTeX metadata" in approval
    assert "get_camera_ready_template_fields" in revision
    assert "Required LaTeX metadata block" in revision
    assert "Publication identifier is" in revision
    assert not (SITE / "invitations/venue/camera_ready_revision/content_process_functions/process.py").exists()
    assert not (SITE / "invitations/venue/camera_ready_verification/content_process_functions/process.py").exists()


def test_camera_ready_callbacks_consume_the_shared_identity_contract():
    approval = (
        SITE / "python_scripts/invitations/venue/decision/camera_ready_guidance.py"
    ).read_text(encoding="utf-8")
    revision = (
        SITE / "python_scripts/invitations/venue/camera_ready_revision/postprocess.py"
    ).read_text(encoding="utf-8")

    assert "fields['camera_ready_dates_block']" in approval
    for field in (
        "camera_ready_accepted_year",
        "camera_ready_volume",
        "camera_ready_publication_id",
        "camera_ready_dates_block",
    ):
        assert f"fields['{field}']" in revision
    assert "http://jmlr.org/papers/v{volume}/{paper_id}.html" in revision


def test_camera_ready_postprocess_adds_exact_paper_verification_guidance():
    reply = load("invitations/venue/camera_ready_revision/edit/reply.json")
    assert len(reply["invitation"]["postprocesses"]) == 1
    assert "camera_ready_revision/postprocess.py" in reply["invitation"]["postprocesses"][0]["script"]
    overlay = load("invitations/venue/camera_ready_revision/invitation/invitation.json")
    assert overlay == {"postprocesses": []}

    callback = (
        SITE / "python_scripts/invitations/venue/camera_ready_revision/postprocess.py"
    ).read_text(encoding="utf-8")
    for expected in (
        "Required LaTeX metadata block",
        "Accepted OpenReview title",
        "Journal of Machine Learning Research",
        "pages 1-last page",
        "Publication identifier is",
        "CC-BY 4.0",
        "PDF content matches the accepted paper",
        "Official Comment",
        "Official JMLR Author Guidelines",
        "camera_ready_author_guidelines",
    ):
        assert expected in callback
    assert "camera_ready_template_fields.py" in callback
    assert "govern wherever they differ from the general guide" in callback
    assert "author list" not in callback.lower()
