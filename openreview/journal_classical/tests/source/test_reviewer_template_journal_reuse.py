"""Reviewer messaging reuses the installed ``openreview.journal`` owners."""

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
LOCAL_TEMPLATES = ROOT / "site_config" / "email_templates" / "reviewer"
JOURNAL_DIR = ROOT.parent / "journal"
_TEMPLATE_SPEC = importlib.util.spec_from_file_location(
    "jmlr_test_journal_templates", JOURNAL_DIR / "templates.py"
)
assert _TEMPLATE_SPEC and _TEMPLATE_SPEC.loader
journal_templates = importlib.util.module_from_spec(_TEMPLATE_SPEC)
_TEMPLATE_SPEC.loader.exec_module(journal_templates)


@pytest.mark.parametrize(
    "filename",
    (
        "assignment.txt",
        "invitation_assignment.txt",
        "resubmission_assignment.txt",
        "review_reminder.txt",
        "unassignment.txt",
    ),
)
def test_local_reviewer_template_override_is_absent(filename):
    assert not (LOCAL_TEMPLATES / filename).exists()


@pytest.mark.parametrize(
    "template_name",
    (
        "reviewer_assignment_email_template",
        "reviewer_invitation_assignment_email_template",
        "reviewer_unassignment_email_template",
    ),
)
def test_journal_supplies_generic_reviewer_templates(template_name):
    template = getattr(journal_templates, template_name)
    assert isinstance(template, str)
    assert template.strip()


@pytest.mark.parametrize(
    "relative,markers",
    (
        (
            "process/reviewer_assignment_process.py",
            ("post_message", "assignment_email_template_script", "unassignment_email_template_script"),
        ),
        (
            "process/reviewer_invitation_assignment_process.py",
            ("post_message", "invitation_assignment_email_template_script"),
        ),
        (
            "process/reviewer_reminder_process.py",
            ("post_message", "get_late_invitees"),
        ),
        (
            "process/review_reminder_with_no_ACK_process.py",
            ("post_message", "get_late_invitees"),
        ),
    ),
)
def test_journal_owns_reviewer_message_process(relative, markers):
    source = (JOURNAL_DIR / relative).read_text(encoding="utf-8")
    for marker in markers:
        assert marker in source


def test_resubmission_reuses_ordinary_journal_assignment_hook():
    """Journal has no separate reviewer-resubmission template hook to override."""
    source = (JOURNAL_DIR / "process/reviewer_assignment_process.py").read_text(
        encoding="utf-8"
    )
    assert "assignment_email_template_script" in source
    assert "resubmission_assignment_email_template_script" not in source
    assert not hasattr(journal_templates, "reviewer_resubmission_assignment_email_template")
