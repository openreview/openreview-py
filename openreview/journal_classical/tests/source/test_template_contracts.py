"""Every retained template must have something that will actually send it.

Journal reads its wording from group content, not from files, and each hook is a
plain ``.format()`` string -- despite the ``_script`` suffix -- filled from a
fixed set of fields at one call site. Two failure modes follow, and neither is
visible by reading the template:

* a field journal does not pass raises ``KeyError`` when the message is sent, so
  the wording is not merely wrong, the notification is lost;
* wording with no hook and no JMLR sender is dead text that reads like
  configuration.

Templates without a current sender are deleted. The small retained set is
classified here so dead wording cannot quietly return as configuration.

See ``docs/system/integration_design/lean-journal-delta.md``.
"""

import string
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

import pytest

ROOT = Path(__file__).resolve().parents[2]
SITE_CONFIG = ROOT / "site_config"
UPSTREAM_COMMIT = "7a8724e04df6b90e65547bcd69244f05986cb111"
UPSTREAM_AUDIT_DATE = "2026-08-15"
UPSTREAM_BLOB = f"https://github.com/openreview/openreview-py/blob/{UPSTREAM_COMMIT}"


@dataclass(frozen=True, slots=True)
class NativeHookContract:
    hook: str
    group: str
    fields: frozenset[str]
    source: str


def native_hook(hook: str, group: str, fields: set[str], source: str) -> NativeHookContract:
    return NativeHookContract(hook, group, frozenset(fields), source)


# Immutable and verified field-compatible with the hook it overrides.
JOURNAL_HOOKS = MappingProxyType({
    "email_templates/ae/camera_ready_verification.txt": native_hook(
        "camera_ready_verification_email_template_script", "Action_Editors",
        {"short_name", "submission_number", "submission_title", "invitation_url"},
        f"{UPSTREAM_BLOB}/openreview/journal/process/camera_ready_revision_process.py",
    ),
    "email_templates/ae/review_rating_starts.txt": native_hook(
        "review_rating_starts_email_template_script", "Action_Editors",
        {"short_name", "submission_number", "submission_title", "website", "decision_period_length", "decision_duedate", "invitation_url", "contact_info"},
        f"{UPSTREAM_BLOB}/openreview/journal/process/review_process.py",
    ),
    "email_templates/author/new_submission.txt": native_hook(
        "new_submission_email_template_script", "Authors",
        {"short_name", "submission_id", "submission_number", "submission_title"},
        f"{UPSTREAM_BLOB}/openreview/journal/process/submission_process.py",
    ),
    "email_templates/author/decision_accept_as_is.txt": native_hook(
        "decision_accept_as_is_email_template_script", "Authors",
        {"short_name", "submission_id", "submission_number", "submission_title", "camera_ready_duedate"},
        f"{UPSTREAM_BLOB}/openreview/journal/process/decision_approval_process.py",
    ),
    "email_templates/author/decision_accept_revision.txt": native_hook(
        "decision_accept_revision_email_template_script", "Authors",
        {"short_name", "submission_id", "submission_number", "submission_title", "camera_ready_duedate"},
        f"{UPSTREAM_BLOB}/openreview/journal/process/decision_approval_process.py",
    ),
})

# JMLR code sends these; journal has no hook and no equivalent message.
JMLR_OWNED = {
    "email_templates/ae/camera_ready_verification_reminder.txt": "JMLR preserves the overdue Action Editor verification reminder",
    "email_templates/ae/camera_ready_verification_reminder_subject.txt": "JMLR preserves the overdue verification reminder subject",
    "email_templates/ae/assignment_initial.txt": "Journal has one AE assignment hook while JMLR distinguishes an initial paper",
    "email_templates/ae/assignment_continuity.txt": "JMLR identifies a prior AE on the linked previous submission",
    "email_templates/author/camera_ready_revision_reminder.txt": "JMLR preserves the overdue author camera-ready reminder",
    "email_templates/author/camera_ready_revision_reminder_subject.txt": "JMLR preserves the overdue camera-ready reminder subject",
    "email_templates/author/decision_subject.txt": "JMLR reject branches share one external decision subject",
    "email_templates/reviewer/assignment_initial.txt": "Journal has one reviewer assignment hook while JMLR distinguishes an initial paper",
    "email_templates/reviewer/assignment_continuity.txt": "JMLR identifies a prior reviewer on the linked previous submission",
    "email_templates/production_editor/final_record_ready.txt": "private production handoff after Journal public release",
    "email_templates/production_editor/final_record_ready_subject.txt": "private production handoff subject after Journal public release",
    "email_templates/production_editor/production_change.txt": "JMLR notifies production after post-acceptance record changes",
    "email_templates/production_editor/production_change_subject.txt": "JMLR production follow-up uses an external subject",
    "email_templates/author/decision_reject_with_resubmission.txt": "journal exposes one reject hook; the second wording needs a JMLR branch",
    "email_templates/author/decision_reject_without_resubmission.txt": "JMLR reject branch distinguishes the terminal outcome explicitly",
    "email_templates/journal_request/action_editor_recruitment.txt": "Journal Request builder accepts a venue-specific Action Editor body default",
    "email_templates/journal_request/reviewer_recruitment.txt": "Journal Request builder accepts a venue-specific reviewer body default",
    "message_templates/eic/assignment_overview_load_failure.html": "EIC assignment overview exposes one standalone load failure message",
}


def templates() -> list[str]:
    return sorted(
        str(path.relative_to(SITE_CONFIG))
        for area in ("email_templates", "message_templates")
        for path in (SITE_CONFIG / area).rglob("*")
        if path.is_file()
    )


def template_fields(relative: str) -> set[str]:
    text = (SITE_CONFIG / relative).read_text(encoding="utf-8")
    # {{{{fullname}}}} is an escaped literal that OpenReview resolves at delivery,
    # not a format field; Formatter.parse applies the escaping rules correctly.
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_every_template_is_classified():
    classified = set(JOURNAL_HOOKS) | set(JMLR_OWNED)
    present = set(templates())
    assert not present - classified, f"unclassified templates: {sorted(present - classified)}"
    assert not classified - present, f"classified but absent: {sorted(classified - present)}"


@pytest.mark.parametrize("relative,contract", sorted(JOURNAL_HOOKS.items()))
def test_native_hook_templates_use_only_pinned_upstream_fields(relative, contract):
    unsupported = sorted(template_fields(relative) - contract.fields)
    assert not unsupported, (
        f"{relative} uses fields upstream never passes to {contract.hook}: {unsupported}. "
        "Sending it would raise KeyError and the notification would be lost."
    )
    rendered = (SITE_CONFIG / relative).read_text(encoding="utf-8").format(
        **{field: f"value-{field}" for field in contract.fields}
    )
    assert "{{fullname}}" in rendered


def test_native_hook_contract_has_immutable_provenance():
    assert UPSTREAM_AUDIT_DATE == "2026-08-15"
    with pytest.raises(TypeError):
        JOURNAL_HOOKS["new"] = None
    for contract in JOURNAL_HOOKS.values():
        assert contract.group in {"Authors", "Action_Editors"}
        assert contract.hook.endswith("_email_template_script")
        assert f"/blob/{UPSTREAM_COMMIT}/" in contract.source
        assert not any(ref in contract.source for ref in ("/main/", "/master/", "/HEAD/"))


def test_every_classification_carries_a_reason():
    """A bare category is not a decision; the reason is what survives review."""
    for relative, reason in JMLR_OWNED.items():
        assert len(reason.split()) >= 4, f"{relative} needs a real reason, got {reason!r}"


def test_minor_revision_email_uses_camera_ready_and_ae_only_verification():
    body = (SITE_CONFIG / "email_templates/author/decision_accept_revision.txt").read_text()
    lowered = body.lower()

    assert "accepted with minor revision" in lowered
    assert "camera ready revision" in lowered
    assert "{submission_id}" in body
    assert "{camera_ready_duedate}" in body
    assert "action editor's decision comments" in lowered
    assert "action editor alone" in lowered
    assert "will not return to reviewers for re-review" in lowered
    assert "official comment" in lowered
    assert "camera-ready revision summary" in lowered
    assert "do not select reviewers or public readers" in lowered
    assert "{{CAMERA_READY_AUTHOR_GUIDELINES_URL}}" in body
    assert "exact paper-specific" in lowered
    assert "camera ready revision form" in lowered
    assert "\\jmlropenreviewdates" not in body
    assert "deanonym" not in lowered
    assert "code" not in lowered
    assert "video" not in lowered


def test_accept_as_is_email_uses_camera_ready_on_the_same_paper():
    body = (SITE_CONFIG / "email_templates/author/decision_accept_as_is.txt").read_text()
    lowered = body.lower()

    assert "accepted as is" in lowered
    assert "camera ready revision" in lowered
    assert "{submission_id}" in body
    assert "{camera_ready_duedate}" in body
    assert "action editor" in lowered
    assert "resubmission" not in lowered
    assert "{{CAMERA_READY_AUTHOR_GUIDELINES_URL}}" in body
    assert "exact paper-specific" in lowered
    assert "camera ready revision form" in lowered
    assert "\\jmlropenreviewdates" not in body
    assert "deanonym" not in lowered
    assert "code" not in lowered
    assert "video" not in lowered


def test_ae_camera_ready_email_uses_official_comment_for_corrections():
    body = (SITE_CONFIG / "email_templates/ae/camera_ready_verification.txt").read_text()
    lowered = body.lower()

    assert "camera-ready revision summary" in lowered
    assert "do not approve" in lowered
    assert "official comment" in lowered
    assert "wait for a corrected upload" in lowered
    assert "{{CAMERA_READY_AUTHOR_GUIDELINES_URL}}" in body
    assert "exact paper-specific" in lowered
    assert "verification form" in lowered
    assert "\\jmlropenreviewdates" not in body
    assert "request a camera-ready revision through the verification form" not in lowered


def test_encouraged_reject_email_uses_the_linked_regular_resubmission_action():
    body = (
        SITE_CONFIG / "email_templates/author/decision_reject_with_resubmission.txt"
    ).read_text()
    lowered = body.lower()

    assert "rejected, with encouragement to resubmit" in lowered
    assert "resubmit from the paper forum below" in lowered
    assert "{paper_url}" in body
    assert "start resubmission" in lowered
    assert "linked regular-track submission" in lowered
    assert "previous jmlr submission field" not in lowered
    assert "pdf response" not in lowered
    assert "immediately attempts" not in lowered


def test_terminal_reject_email_exposes_no_resubmission_action():
    body = (
        SITE_CONFIG / "email_templates/author/decision_reject_without_resubmission.txt"
    ).read_text()
    lowered = body.lower()

    assert "decision of reject" in lowered
    assert "{paper_url}" in body
    assert "terminal" in lowered
    assert "no resubmission action" in lowered
    assert "start resubmission" not in lowered


def test_author_new_submission_template_uses_journal_process_fields_only():
    body = (SITE_CONFIG / "email_templates/author/new_submission.txt").read_text()

    assert "{short_name}" in body
    assert "{submission_id}" in body
    assert "{submission_number}" in body
    assert "{submission_title}" in body
    assert "{receipt_intro}" not in body
    assert "{paper_url}" not in body


def test_submission_postprocess_starts_with_python_entry_point():
    body = (
        SITE_CONFIG / "python_scripts/invitations/venue/submission/postprocess.py"
    ).read_text()

    assert body.lstrip().startswith("def process(")
    assert "ensure_previous_submission_access_for_current_ae" in body
    assert "openreview.tools.get_invitation" in body
    assert "if revision:" in body
