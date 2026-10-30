"""Focused source contracts for the accepted JMLR-over-Journal deltas."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site_config"


def text(relative):
    return (SITE / relative).read_text(encoding="utf-8")


def settings():
    return json.loads(text("openreview.json"))["defaults"]


def test_submission_uses_journal_authors_and_required_immutable_track():
    fields = settings()["request_form"]["submission_additional_fields"]
    assert "author_list" not in fields
    assert "authorids" not in fields  # Journal owns the standard profile picker and instructions.
    assert fields["track_id"]["value"]["param"] == {
        "type": "string", "input": "select", "enum": ["Regular", "OSS", "Award"],
        "default": "Regular", "optional": False,
    }
    assert fields["supplementary_material"]["value"]["param"]["maxSize"] == 10
    assert fields["code"]["value"]["param"] == {
        "type": "string",
        "regex": "^https?://.+$",
        "optional": True,
        "deletable": True,
    }
    assert "JMLR/Reviewers/Paper${4/number}" in fields["supplementary_material"]["readers"]
    submission_preprocess = text("python_scripts/invitations/venue/submission/preprocess.py")
    assert "Track is immutable after submission" in submission_preprocess
    assert "previous_JMLR_submission_url" in submission_preprocess
    assert "Resubmission track must match the previous paper" in submission_preprocess
    assert "if requested != inherited:" in submission_preprocess
    assert "note.content['track_id'] = {'value': inherited}" not in submission_preprocess
    submission_postprocess = text("python_scripts/invitations/venue/submission/postprocess.py")
    assert "expected_link = f'[Paper {previous.number}]({previous_url})'" in submission_postprocess
    assert "'previous_JMLR_submission': {'value': expected_link}" in submission_postprocess
    assert "await_process=True" in submission_postprocess
    assert "note.content.pop('previous_JMLR_submission', None)" in submission_preprocess
    assert fields["previous_JMLR_submission"]["value"]["param"] == {
        "type": "string", "optional": True, "deletable": True,
        "markdown": True, "hidden": True,
    }
    assert "get_revision_id" in text("python_scripts/invitations/venue/submission/postprocess.py")
    assert "get_camera_ready_revision_id" in text("python_scripts/invitations/venue/decision/camera_ready_guidance.py")
    assert "get_eic_revision_id" in text("python_scripts/invitations/venue/accepted/postprocess.py")
    for callback in (
        "python_scripts/invitations/venue/submission/postprocess.py",
        "python_scripts/invitations/venue/decision/camera_ready_guidance.py",
        "python_scripts/invitations/venue/accepted/postprocess.py",
    ):
        assert "pop('code'" not in text(callback)
    assert "code" not in submission_preprocess
    assert "cover_letter" not in submission_preprocess
    assert "supplementary_material" not in submission_preprocess


def test_active_eligibility_is_public_and_expired_history_is_private():
    for name in ("regular_ineligible", "track_eligible"):
        invitation = json.loads(text(f"invitations/action_editors/{name}/invitation/invitation.json"))
        assert invitation["readers"] == ["everyone"]
        preprocess = text(f"invitations/action_editors/{name}/process_functions/preprocess.py")
        assert "['JMLR/Editors_In_Chief', edge.tail] if edge.ddate else ['everyone']" in preprocess
        assert "not edge.ddate and edge.tail not in active" in preprocess


def test_assignment_delegates_native_gates_then_enforces_continuity_and_track_pool():
    assignment = text("invitations/action_editors/assignment/process_functions/preprocess.py")
    continuity = assignment.index("continuity = not edge.ddate")
    native = assignment.index("journal_preprocess.process")
    eligibility = assignment.index("Regular_Ineligible")
    assert continuity < native < eligibility
    assert assignment.count("journal_preprocess.process") == 1
    assert "openreview.journal.Journal = lambda: journal" in assignment
    assert "get_action_editors_id" in assignment
    assert "get_ae_max_papers" not in assignment
    assert "get_ae_custom_max_papers_id" not in assignment
    postprocess = text("python_scripts/invitations/venue/submission/postprocess.py")
    assert "compute_conflicts" in postprocess
    assert "get_ae_availability_id" not in postprocess
    assert "Regular_Ineligible" not in postprocess


def test_author_recommendations_are_jmlr_scheduled_for_new_regular_only():
    assert settings()["request_form"]["skip_ac_recommendation"] is True
    recommendation = text("invitations/action_editors/recommendation/process_functions/preprocess.py")
    assert "only collected for Regular submissions" in recommendation
    assert "not collected for resubmissions" in recommendation
    assert "Regular_Ineligible" in recommendation
    assert "Assignment_Availability" not in recommendation


def test_only_permitted_regular_decisions_can_be_resubmitted():
    decision_fields = settings()["request_form"]["decision_additional_fields"]
    resubmission = decision_fields["resubmission_of_major_revision"]
    assert decision_fields["recommendation"]["value"]["param"]["enum"] == [
        "Accept as is", "Accept with minor revision", "Reject"
    ]
    assert resubmission["value"]["param"] == {
        "type": "string",
        "enum": ["Reject with encouragement to resubmit"],
        "input": "checkbox",
        "optional": True,
        "deletable": True,
    }
    preprocess = text("python_scripts/invitations/venue/submission/preprocess.py")
    rejected = text("invitations/venue/rejected/process_functions/process.py")
    assert "available only for Regular papers" in preprocess
    assert "does not permit resubmission" in preprocess
    assert "resubmission_of_major_revision" in preprocess
    assert "resubmission_of_major_revision" in rejected
    assert "if not permitted:" in rejected
    assert "Paper{submission.number}/-/Resubmission" in rejected
    assert "decision_reject_with_resubmission.txt" in rejected
    assert "decision_reject_without_resubmission.txt" in rejected


def test_resubmission_route_keeps_journal_editor_but_makes_linkage_explicit():
    homepage = text("global_settings/jmlr_meta.js")
    web = text("python_scripts/invitations/venue/resubmission/web.js")
    rejected = text("invitations/venue/rejected/process_functions/process.py")
    for required in (
        "previous_JMLR_submission_url",
        "var draftUsers = ['guest', user.id]",
        "globalThis.localStorage.setItem",
        "globalThis.location.replace",
    ):
        assert required in web
    assert "view2.mkNewNoteEditor" not in web
    assert "authorids" not in web
    assert "profile{}" not in web
    assert "component: 'VenueHomepage'" in homepage
    assert "Resubmission for JMLR Paper" in homepage
    assert "This native Journal submission form" in homepage
    assert "Regular (inherited)" in homepage
    assert "a different selection is rejected" in homepage
    assert "searchable Authors control" in homepage
    assert "jmlr-resubmission-inherited-context" in homepage
    assert "PYTHON_SCRIPT_JSON:invitations/venue/resubmission/web.js" in rejected
    assert "f'{{SITE_URL}}/invitation?'" in rejected
    assert "Webfield2.api.get('/notes'" not in web


def test_ae_removal_blocks_active_assignments_and_privatises_history():
    guard = text("invitations/venue/manage_action_editors/process_functions/preprocess.py")
    cleanup = text("invitations/venue/manage_action_editors/process_functions/process.py")
    assert "journal.is_active_submission" in guard
    assert "Reassign active papers" in guard
    assert "readers=['JMLR/Editors_In_Chief', member]" in cleanup
    assert "get_ae_availability_id" not in cleanup


def test_role_manager_does_not_load_or_filter_availability():
    web = text("invitations/venue/manage_action_editors/web/web.js")
    assert "Assignment_Availability" not in web
    assert 'data-track="' in web
    assert "JMLR/Action_Editors/-/Track_Eligible" in web
    assert "jmlr-save" in web
    assert "jmlr-remove" in web
    assert "Webfield2.api.post" in web
    assert "/groups/edits?awaitProcess=true" in web
    assert "tracks = ['Regular']" in web
    assert "preferredEmail" in web
    role_web = text("invitations/venue/role_management/web/web.js")
    assert "Webfield2.api.get('/groups'" in role_web


def test_eic_compatibility_console_uses_exact_assignment_queries_and_tabs():
    web = text("global_settings/jmlr_eic_compatibility_landing.js")

    for destination in (
        "JMLR/Action_Editors/-/Assignment",
        "JMLR/Reviewers/-/Assignment",
        "/forum?id={{PROD_JOURNAL_ID}}",
        "JMLR/Reviewers/-/Reviewer_Report",
        "'/group/edit?id=' + encodeURIComponent(eic)",
        "'/group/edit?id=' + encodeURIComponent(reviewers)",
        "'/group/edit?id=' + encodeURIComponent(productionEditors)",
        "JMLR%2F-%2FManage_Action_Editors",
        "'/group?id=' + encodeURIComponent(actionEditors)",
    ):
        assert destination in web

    assert "JMLR/Reviewers/-/Reviewer_Report" in web
    assert "Webfield2.ui.setup('#group-container'" in web
    assert "JMLR Editors-in-Chief Console" in web
    assert "tabs: ['Pending Tasks', 'All Submissions', 'Assignments', 'Recruitment', 'Role Management']" in web
    assert "Webfield2.api.getAllSubmissions(submissionInvitation, { domain: venue })" in web
    assert "Webfield2.api.get('/invitations', {" in web
    assert "invitee: eic, domain: venue, expired: false, select: 'id', stream: true" in web
    assert "Webfield2.api.get('/edges', { invitation: aeAssignment, domain: venue, stream: true })" in web
    assert "Webfield2.api.get('/edges', { invitation: reviewerAssignment, domain: venue, stream: true })" in web
    assert "jmlr-assignment-search" in web
    assert "jmlr-stage-filter" in web
    assert "data-stage" in web
    assert "No Editors-in-Chief tasks require action" in web
    assert "Webfield2.ui.done()" in web

    for forbidden in (
        "prefix:",
        "$.get",
        "fetch(",
        "Active Papers",
        "Proposed Action Editor assignments",
        "'/assignments?group='",
        '"/assignments?group=',
        "list-inline mb-0",
    ):
        assert forbidden not in web


def test_production_is_private_handoff_without_public_jmlr_link_or_state():
    postprocess = text("python_scripts/invitations/venue/accepted/postprocess.py")
    invitation = json.loads(text("invitations/venue/download_publication_files/invitation/invitation.json"))
    assert invitation["readers"] == ["JMLR/Editors_In_Chief", "JMLR/Production_Editors"]
    assert "client.post_message" in postprocess
    assert "Production_Editors" in postprocess
    assert "public_urls" in postprocess
    assert "Mark_as_Published" not in postprocess
    assert "required_message_delivery" not in postprocess
    assert "canonical" not in postprocess.lower()


def test_publication_status_reply_targets_a_submission_and_preprocess_binds_same_root():
    reply = json.loads(text("invitations/venue/publication_status/edit/reply.json"))
    assert reply["note"]["forum"] == {
        "param": {"withInvitation": "JMLR/-/Submission"}
    }
    assert reply["note"]["replyto"] == {
        "param": {"withInvitation": "JMLR/-/Submission"}
    }
    preprocess = text("python_scripts/invitations/venue/publication_status/preprocess.py")
    assert "note.replyto != submission.id" in preprocess
    assert "journal.accepted_venue_id" in preprocess
    assert "get_accepted_venue_id" not in preprocess


def test_publication_projection_has_one_helper_and_no_track_website_alias():
    config = settings()
    assert config["tracks"]["OSS"]["publication"] == {"special_issue": "MLOSS"}
    assert all("url" not in track and "track_url" not in track for track in config["tracks"].values())

    postprocess = text("python_scripts/invitations/venue/accepted/postprocess.py")
    assert "PYTHON_SCRIPT_JSON:invitations/venue/publication_metadata.py" in postprocess
    assert "{{TRACK_PUBLICATION_POLICY_JSON}}" in postprocess
    assert "build_publication_metadata" in postprocess
    assert "'special_issue'" not in postprocess
    assert "'extra_links'" not in postprocess
    assert "track_url" not in postprocess


def test_every_python_delta_compiles():
    for path in SITE.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "openreview.journal.Journal()" not in source
        compile(source, str(path), "exec")
