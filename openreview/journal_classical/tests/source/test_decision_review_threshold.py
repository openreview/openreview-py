"""JMLR opens Journal's Decision action at the accepted 2/1 thresholds."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROCESS = (
    ROOT
    / "site_config"
    / "invitations"
    / "venue"
    / "review"
    / "content_process_functions"
    / "process.py"
)


def source() -> str:
    return PROCESS.read_text(encoding="utf-8")


def integer_constants() -> dict[str, int]:
    tree = ast.parse(source())
    constants: dict[str, int] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, int):
                constants[target.id] = node.value.value
    return constants


def test_first_submission_and_resubmission_thresholds_are_two_and_one():
    constants = integer_constants()
    assert constants["FIRST_SUBMISSION_DECISION_MINIMUM_REVIEWS"] == 2
    assert constants["RESUBMISSION_DECISION_MINIMUM_REVIEWS"] == 1


def test_threshold_is_track_independent_and_resubmission_is_link_backed():
    text = source()
    threshold_block = text.split("is_resubmission = bool(", 1)[1]
    assert "previous_JMLR_submission_url" in threshold_block
    assert "previous_JMLR_submission" in threshold_block
    assert "track_id" not in threshold_block


def test_journal_reviewer_target_and_decision_builder_are_reused():
    text = source()
    assert "len(reviews) == journal.get_number_of_reviewers()" in text
    assert "journal.release_reviews_process(submission)" in text
    assert "journal.invitation_builder.set_note_decision_invitation(" in text
    assert "journal.get_decision_period_length()" in text


def test_existing_decision_and_review_edits_do_not_repeat_threshold_effects():
    text = source()
    assert "if edit.id != review_edits[0].id:" in text
    assert "client.get_invitation(decision_id)" in text
    assert "details.get('name') != 'NotFoundError'" in text


def test_replacement_preserves_native_review_side_effects_and_idempotent_delete_load():
    text = source()
    for contract in (
        "journal.notify_readers(edit)",
        "journal.get_reviewer_pending_review_id()",
        "journal.get_reviewer_assignment_acknowledgement_id(",
        "journal.invitation_builder.expire_invitation(",
        "journal.get_release_review_id(number=submission.number)",
        "journal.release_reviews_process(submission)",
    ):
        assert contract in text
    assert "expected_pending = sum(" in text
    assert "journal.get_reviewer_assignment_id()" in text
    assert "if pending_edges and pending_edges[0].weight != expected_pending:" in text
    assert "pending_edges[0].weight += 1" not in text
