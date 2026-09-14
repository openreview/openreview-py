"""Unit coverage for the JMLR-owned camera-ready metadata helper."""

import datetime
from types import SimpleNamespace
from pathlib import Path


SITE = Path(__file__).resolve().parents[2] / "site_config"
SOURCE = SITE / "python_scripts/invitations/venue/camera_ready_template_fields.py"
NAMESPACE = {}
exec(SOURCE.read_text(encoding="utf-8"), NAMESPACE)
get_camera_ready_template_fields = NAMESPACE["get_camera_ready_template_fields"]


def millis(year, month, day):
    value = datetime.datetime(year, month, day, tzinfo=datetime.timezone.utc)
    return int(value.timestamp() * 1000)


def note(note_id, number, created, previous=None):
    content = {}
    if previous:
        content["previous_JMLR_submission_url"] = {
            "value": f"https://openreview.net/forum?id={previous}"
        }
    return SimpleNamespace(
        id=note_id, number=number, cdate=created, tcdate=created, content=content
    )


def test_fields_follow_submission_chain_and_pad_paper_number():
    original = note("original", 17, millis(2024, 5, 2))
    current = note("current", 6727, millis(2026, 3, 9), previous="original")
    decision = SimpleNamespace(cdate=millis(2026, 8, 15), tcdate=millis(2026, 8, 15))
    client = SimpleNamespace(get_note=lambda note_id: {"original": original}[note_id])
    journal = SimpleNamespace(short_name="JMLR")

    assert get_camera_ready_template_fields(client, journal, current, decision) == {
        "camera_ready_submitted": "5/24",
        "camera_ready_revised": "3/26",
        "camera_ready_accepted": "8/26",
        "camera_ready_accepted_year_short": "26",
        "camera_ready_submission_number_padded": "06727",
        "camera_ready_accepted_year": 2026,
        "camera_ready_volume": 27,
        "camera_ready_publication_id": "26-06727",
        "camera_ready_dates_block": (
            "\\jmlropenreviewdates{\n"
            "  submitted = {5/24},\n"
            "  revised = {3/26},\n"
            "  accepted = {8/26},\n"
            "  paperid = {26-06727}\n"
            "}"
        ),
    }


def test_first_submission_uses_acceptance_month_as_revised_month():
    current = note("current", 123456, millis(2026, 3, 9))
    decision = SimpleNamespace(cdate=millis(2026, 8, 15), tcdate=millis(2026, 8, 15))
    client = SimpleNamespace(get_note=lambda _note_id: None)
    journal = SimpleNamespace(short_name="JMLR")

    fields = get_camera_ready_template_fields(client, journal, current, decision)
    assert fields["camera_ready_submitted"] == "3/26"
    assert fields["camera_ready_revised"] == "8/26"
    assert fields["camera_ready_submission_number_padded"] == "23456"
    assert fields["camera_ready_accepted_year"] == 2026
    assert fields["camera_ready_volume"] == 27
    assert fields["camera_ready_publication_id"] == "26-23456"


def test_jmlr_callbacks_embed_deployable_camera_ready_helper():
    helper = SOURCE
    expected_include = "PYTHON_SCRIPT_JSON:invitations/venue/camera_ready_template_fields.py"

    assert "get_camera_ready_template_fields" in helper.read_text(encoding="utf-8")
    for relative in (
        "python_scripts/invitations/venue/decision/camera_ready_guidance.py",
        "python_scripts/invitations/venue/camera_ready_revision/postprocess.py",
        "python_scripts/invitations/venue/accepted/postprocess.py",
    ):
        callback = (SITE / relative).read_text(encoding="utf-8")
        assert expected_include in callback
        assert "openreview.journal.get_camera_ready_template_fields" not in callback
        assert "template_field_namespace = {}" in callback


def test_exact_fields_stay_on_jmlr_owned_invitation_descriptions():
    author = (SITE / "python_scripts/invitations/venue/decision/camera_ready_guidance.py").read_text()
    verification = (SITE / "python_scripts/invitations/venue/camera_ready_revision/postprocess.py").read_text()

    assert "camera_ready_dates_block" in author
    assert "camera_ready_dates_block" in verification
    for marker in ("camera_ready_submitted", "camera_ready_revised", "camera_ready_accepted"):
        assert marker in verification
    assert "paper_url" in verification


def test_consumers_use_shared_identity_fields_without_local_constructors():
    callbacks = {
        name: (SITE / name).read_text(encoding="utf-8")
        for name in (
            "python_scripts/invitations/venue/decision/camera_ready_guidance.py",
            "python_scripts/invitations/venue/camera_ready_revision/postprocess.py",
            "python_scripts/invitations/venue/accepted/postprocess.py",
        )
    }

    assert "camera_ready_dates_block" in callbacks[
        "python_scripts/invitations/venue/decision/camera_ready_guidance.py"
    ]
    for name in (
        "python_scripts/invitations/venue/camera_ready_revision/postprocess.py",
        "python_scripts/invitations/venue/accepted/postprocess.py",
    ):
        assert "camera_ready_accepted_year" in callbacks[name]
        assert "camera_ready_volume" in callbacks[name]
        assert "camera_ready_publication_id" in callbacks[name]
    for source in callbacks.values():
        assert "dates_block = (" not in source
        assert "publication_id = f" not in source
        assert "accepted_year = datetime.datetime.fromtimestamp" not in source
