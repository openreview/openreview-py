"""Focused source contract for the JMLR EIC compatibility landing."""

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "site_config/global_settings/jmlr_eic_compatibility_landing.js"


@pytest.fixture(scope="module")
def source():
    return SOURCE.read_text(encoding="utf-8")


def test_landing_uses_five_focused_tabs_and_exact_data_queries(source):
    assert "tabs: ['Pending Tasks', 'All Submissions', 'Assignments', 'Recruitment', 'Role Management']" in source
    assert "getAllSubmissions(submissionInvitation, { domain: venue })" in source
    assert "invitee: eic, domain: venue, expired: false, select: 'id', stream: true" in source
    assert "invitation: aeAssignment, domain: venue, stream: true" in source
    assert "invitation: reviewerAssignment, domain: venue, stream: true" in source
    assert "jmlr-assignment-search" in source
    assert "jmlr-stage-filter" in source


def test_all_submission_columns_wrap_without_overlapping(source):
    assert "jmlr-eic-table" in source
    assert "table-layout: fixed" in source
    assert "overflow-wrap: anywhere" in source
    assert "min-width: 850px" in source


def test_landing_delegates_actions_to_exact_owners(source):
    for marker in (
        "JMLR/Action_Editors/-/Assignment",
        "JMLR/Reviewers/-/Assignment",
        "/forum?id={{PROD_JOURNAL_ID}}",
        "JMLR/Reviewers/-/Reviewer_Report",
        "JMLR%2F-%2FManage_Action_Editors",
        "JMLR%2F-%2FManage_Tracks",
        "'/group/edit?id=' + encodeURIComponent(eic)",
        "'/group/edit?id=' + encodeURIComponent(reviewers)",
        "'/group/edit?id=' + encodeURIComponent(productionEditors)",
    ):
        assert marker in source


def test_landing_uses_invitee_bounded_tasks_without_prefix_discovery_or_mutation(source):
    assert "Webfield2.api.get('/invitations'" in source
    assert "invitee: eic" in source
    assert "prefix:" not in source
    assert "Webfield2.api.post" not in source
    assert "/assignments?group=JMLR/Action_Editors" not in source
    assert "Proposed Action Editor assignments" not in source


def test_landing_excludes_authored_papers_without_conflict_filtering(source):
    assert "isAuthoredByCurrentEic" in source
    assert "!isAuthoredByCurrentEic(submission)" in source
    assert "isConflictedWithCurrentEic" not in source


def test_pending_tasks_keep_decision_recovery_but_not_ae_camera_ready(source):
    assert "'Decision_Approval': 'Review decision'" in source
    assert "'Desk_Rejection_Approval': 'Review desk rejection'" in source
    assert "'Retraction_Approval': 'Review retraction'" in source
    assert "Camera_Ready_Verification" not in source


def test_pending_task_link_rendering_keeps_exact_task_url_and_eic_referrer(source):
    assert "var referrer = encodeURIComponent('[JMLR EIC](/group?id=' + eic + ')');" in source
    assert "<a href=\"/forum?id=' + encodeURIComponent(task.submission.id) + '&referrer=' + referrer + '\">" in source
    assert "escapeHtml(task.label) + '</a>" in source
    assert "alreadyCompleted" in source
    assert "reply.invitations" in source


@pytest.mark.parametrize(
    "relative",
    (
        "eic_console_webfield.js",
        "eic_console_webfield_parts/00_constants.js",
        "eic_console_webfield_parts/10_shared_helpers.js",
        "eic_console_webfield_parts/20_data_loading.js",
        "eic_console_webfield_parts/30_format_status_setup.js",
        "eic_console_webfield_parts/31_format_submission_tasks.js",
        "eic_console_webfield_parts/32_format_return_model.js",
        "eic_console_webfield_parts/40_paper_tables.js",
        "eic_console_webfield_parts/50_availability_and_status_tabs.js",
        "eic_console_webfield_parts/60_role_assignment.js",
        "eic_console_webfield_parts/70_bulk_invite.js",
        "eic_console_webfield_parts/99_render.js",
    ),
)
def test_legacy_console_source_is_absent(relative):
    assert not (SOURCE.parent / relative).exists()
