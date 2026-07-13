from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HUB_PARTS = (
    REPO_ROOT
    / "site_config"
    / "python_scripts"
    / "invitations"
    / "venue"
    / "under_review"
    / "reviewer_assignment_hub_parts"
)
HUB_SOURCE = (
    REPO_ROOT
    / "site_config"
    / "python_scripts"
    / "invitations"
    / "venue"
    / "under_review"
    / "reviewer_assignment_hub.py"
)
HUB_REFRESH_PROCESS = REPO_ROOT / "site_config/invitations/venue/reviewer_assignment_hub_refresh/process_functions/process.py"
PREPROCESS = REPO_ROOT / "site_config/invitations/reviewers/assignment/process_functions/preprocess.py"
ASSIGNMENT_CANDIDATE_CONFLICT_REFRESH_PROCESS = (
    REPO_ROOT
    / "site_config/invitations/venue/assignment_candidate_conflict_refresh/process_functions/process.py"
)
ASSIGNMENT_CONFLICT_MATERIALIZATION = (
    REPO_ROOT / "site_config/python_scripts/invitations/venue/assignment_conflict_materialization.py"
)
ASSIGNMENT_EDGE = REPO_ROOT / "site_config/invitations/reviewers/assignment/edge/edge.json"


def test_reviewer_assignment_browser_contract_names_sources_and_submit_uses_contract_invitation():
    hub_source = HUB_SOURCE.read_text(encoding="utf-8")
    hub_refresh_process = HUB_REFRESH_PROCESS.read_text(encoding="utf-8")
    shared = (HUB_PARTS / "shared_helpers.py").read_text(encoding="utf-8")
    payload_helper = shared[
        shared.index("function reviewerAssignmentEdgePayload(tail, actorSignature, edgeLabel)") :
        shared.index("function postCheckedReviewerAssignmentEdge(tail, actorSignature, edgeLabel, dueDateMillis)")
    ]

    assert "def reviewer_assignment_browser_contract(" in hub_source
    assert "'assignmentBrowserContract': assignment_browser_contract" in hub_source
    assert "auto_assign_config['assignmentBrowserContract'] = assignment_browser_contract" in hub_source
    assert "auto_assign_config.pop('reviewersAssignmentId', None)" in hub_source
    assert "'paper_id': note.id" in hub_source
    assert "'paper_number': note.number" in hub_source
    assert "'assignment_invitation': reviewer_assignment_id" in hub_source
    assert "'deployed_assignment_sources': [\n            reviewer_assignment_id\n        ]" in hub_source
    assert "'readback_assignment_sources': [\n            reviewer_assignment_id,\n            reviewer_invite_assignment_id" in hub_source
    assert "'affinity_score_invitation': journal.get_reviewer_affinity_score_id()" in hub_source
    assert "'openreview_conflict_invitation': journal.get_reviewer_conflict_id()" in hub_source
    assert "'reviewer_availability_invitation': journal.get_reviewer_availability_id()" in hub_source
    assert "'pending_reviews_invitation': journal.get_reviewer_pending_review_id()" in hub_source
    assert "'assignment_history_sources': [\n                reviewer_assignment_id,\n                journal.get_reviewer_assignment_id()" in hub_source
    assert "'legacy_read_only_sources': [\n            journal.get_reviewer_assignment_id()" in hub_source
    assert "'raw_edges_browse_default': False" in hub_source
    assert "/edges/browse" not in hub_source

    assert "function reviewerAssignmentBrowserContract()" in shared
    assert "function reviewerAssignmentInvitationId()" in shared
    assert "reviewerAssignmentBrowserContract().assignment_invitation || AUTO_ASSIGN_CONFIG.reviewersAssignmentId" in shared
    assert "invitation: reviewerAssignmentInvitationId()" in payload_helper
    assert "invitation: AUTO_ASSIGN_CONFIG.reviewersAssignmentId" not in payload_helper

    assert "auto_assign_config['assignmentBrowserContract'] = {" in hub_refresh_process
    assert "'assignment_invitation': reviewer_assignment_id" in hub_refresh_process
    assert "'raw_edges_browse_default': False" in hub_refresh_process
    assert "invitation: reviewerAssignmentInvitationId()" in hub_refresh_process


def test_manual_search_override_posts_checked_assignment_edge_payload_backend_accepts():
    hub_source = HUB_SOURCE.read_text(encoding="utf-8")
    hub_refresh_process = HUB_REFRESH_PROCESS.read_text(encoding="utf-8")
    conflict_refresh_process = ASSIGNMENT_CANDIDATE_CONFLICT_REFRESH_PROCESS.read_text(encoding="utf-8")
    conflict_materialization = ASSIGNMENT_CONFLICT_MATERIALIZATION.read_text(encoding="utf-8")
    shared = (HUB_PARTS / "shared_helpers.py").read_text(encoding="utf-8")
    search = (HUB_PARTS / "search_reviewers_tab.py").read_text(encoding="utf-8")
    auto = (HUB_PARTS / "auto_assign_reviewers_tab.py").read_text(encoding="utf-8")
    previous = (HUB_PARTS / "previous_reviewers_tab.py").read_text(encoding="utf-8")
    preprocess = PREPROCESS.read_text(encoding="utf-8")
    payload_helper = shared[
        shared.index("function reviewerAssignmentEdgePayload(tail, actorSignature, edgeLabel)") :
        shared.index("function postCheckedReviewerAssignmentEdge(tail, actorSignature, edgeLabel, dueDateMillis)")
    ]

    assert "function reviewerAssignmentEdgePayload(tail, actorSignature, edgeLabel)" in shared
    assert "invitation: reviewerAssignmentInvitationId()" in payload_helper
    assert "invitation: AUTO_ASSIGN_CONFIG.reviewersAssignmentId" not in payload_helper
    assert "reviewer_assignment_id = journal.get_reviewer_assignment_id(number=note.number)" in hub_source
    assert "'assignmentBrowserContract': assignment_browser_contract" in hub_source
    assert "auto_assign_config['assignmentBrowserContract'] = assignment_browser_contract" in hub_source
    assert "auto_assign_config.pop('reviewersAssignmentId', None)" in hub_source
    assert "auto_assign_config['reviewersAssignmentId'] = reviewer_assignment_id" in hub_refresh_process
    assert "reviewer_assignment_id = journal.get_reviewer_assignment_id()\n" not in hub_source
    assert "domain:" not in payload_helper
    assert "signatures: [actorSignature]" in payload_helper
    assert "head: AUTO_ASSIGN_CONFIG.noteId" in payload_helper
    assert "tail: tail" in payload_helper
    assert "weight: 1" in payload_helper
    assert "if (edgeLabel) payload.label = edgeLabel;" in payload_helper
    assert "var payload = reviewerAssignmentEdgePayload(tail, actorSignature, edgeLabel);" in shared
    assert "Webfield2.api.post('/edges', payload)" in shared
    assert "error.assignmentPayload = payload;" in shared
    assert "function reviewerAssignmentErrorMessage(error, fallbackMessage)" in shared
    assert "message += ' (' + summary.join('; ') + ')';" in shared
    assert "var rejectionArgs = Array.prototype.slice.call(arguments);" in shared
    assert "if (typeof Promise !== 'undefined' && Promise.reject) return Promise.reject(error);" in shared

    assert "function materializeOnDemandReviewerConflict(tail, actorSignature)" in shared
    assert "AUTO_ASSIGN_CONFIG.venueId + '/-/Assignment_Candidate_Conflict_Refresh'" in shared
    assert "Webfield2.api.post('/notes/edits?awaitProcess=true'" in shared
    assert "candidate_id: { value: tail }" in shared
    assert "role: { value: 'reviewer' }" in shared
    assert "def materialize_openreview_conflicts(" in conflict_materialization
    assert 'assignment_conflict_namespace["has_assignment_conflict"]' in conflict_materialization
    assert 'conflict_type="openreview"' in conflict_materialization
    assert "assignment_conflict_materialization.py" in conflict_refresh_process
    assert "materialize_openreview_conflicts" in conflict_refresh_process
    assert "journal.get_reviewer_conflict_id()" in conflict_refresh_process

    assert "refreshReviewerSearchCandidateConflict(selectedCandidate, signature)" in search
    assert "materializeOnDemandReviewerConflict(candidate.tail, actorSignature)" in search
    assert "postCheckedReviewerAssignmentEdge(tail, signature, reviewerAssignmentOverrideLabel(refreshedCandidate, signature), selectedDueDateMillis)" in search
    assert "reviewerAssignmentOverrideLabel(selectedCandidate, signature)" in search
    assert "reviewerAssignmentErrorMessage(error, 'Unable to assign selected reviewers.')" in search
    assert "if (!newTails.length) {" in search
    assert "The selected reviewers are already assigned. Refreshing..." in search
    assert "message + ' Refreshing current reviewer assignments...'" not in search
    assert "Webfield2.api.post('/edges', {\n                  invitation: AUTO_ASSIGN_CONFIG.reviewersAssignmentId" not in search
    assert "postCheckedReviewerAssignmentEdge(candidate.tail, signature, reviewerAssignmentOverrideLabel(candidate, signature), selectedDueDateMillis)" in auto
    assert "reviewerAssignmentOverrideLabel(candidate, signature)" in auto
    assert "reviewerAssignmentErrorMessage(error, 'Unable to auto-assign reviewers.')" in auto
    assert "message + ' Refreshing current reviewer assignments...'" not in auto
    assert "Webfield2.api.post('/edges', {\n                  invitation: AUTO_ASSIGN_CONFIG.reviewersAssignmentId" not in auto
    assert "return postCheckedReviewerAssignmentEdge(" in previous
    assert "includeConflicted ? 'Previous Reviewer Conflict Override' : undefined,\n                selectedDueDateMillis" in previous
    assert "showReviewerAssignmentComplete(button, 'Assigned ' + reviewerIdsToAssign.length + ' previous reviewer(s).')" in previous
    assert "reviewerAssignmentErrorMessage(error, 'Unable to assign previous reviewers.')" in previous
    assert "Webfield2.api.post('/edges', postBody)" not in previous
    assert "var postBody = {\n                invitation: AUTO_ASSIGN_CONFIG.reviewersAssignmentId" not in previous

    assert "ae_openreview_conflict_override_label = 'AE OpenReview Conflict Override'" in preprocess
    assert "eic_openreview_conflict_override_label = 'EIC OpenReview Conflict Override'" in preprocess
    assert "edge.label in [ae_openreview_conflict_override_label, eic_openreview_conflict_override_label]" in preprocess
    assert "hard_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, edge.tail)" in preprocess
    assert "if hard_conflict:" in preprocess
    assert "if not is_available(availability_edge, now):" in preprocess
    assert "Reviewer {edge.tail} was assigned new paper" in preprocess
    assert "pending_review_count >= max_papers" in preprocess


def test_reviewer_assignment_submit_and_readback_paths_use_contract_invitation_helper():
    shared = (HUB_PARTS / "shared_helpers.py").read_text(encoding="utf-8")
    search = (HUB_PARTS / "search_reviewers_tab.py").read_text(encoding="utf-8")
    auto = (HUB_PARTS / "auto_assign_reviewers_tab.py").read_text(encoding="utf-8")
    previous = (HUB_PARTS / "previous_reviewers_tab.py").read_text(encoding="utf-8")
    candidate_helpers = (HUB_PARTS / "candidate_data_helpers.py").read_text(encoding="utf-8")

    payload_helper = shared[
        shared.index("function reviewerAssignmentEdgePayload(tail, actorSignature, edgeLabel)") :
        shared.index("function defaultReviewerDueDateInputValue()")
    ]
    assert "invitation: reviewerAssignmentInvitationId()" in payload_helper
    assert "AUTO_ASSIGN_CONFIG.reviewersAssignmentId" not in payload_helper

    for source in [search, auto, previous]:
        assert "postCheckedReviewerAssignmentEdge(" in source
        assert "reviewerAssignmentEdgePayload(" in source or "postCheckedReviewerAssignmentEdge(" in source
        assert "invitation: AUTO_ASSIGN_CONFIG.reviewersAssignmentId" not in source
        assert "Webfield2.api.post('/edges', {" not in source

    for readback_source in [search, auto, candidate_helpers]:
        assert "invitation: reviewerAssignmentInvitationId()" in readback_source
        assert "invitation: AUTO_ASSIGN_CONFIG.reviewersAssignmentId" not in readback_source

    assert "reviewerAssignmentInvitationId(),\n    AUTO_ASSIGN_CONFIG.venueId + '/Reviewers/-/Archived_Assignment'" in previous
    assert "function waitForReviewerRemovalReadback(removedReviewerTails, options)" in candidate_helpers
    removal_readback = candidate_helpers[
        candidate_helpers.index("function waitForReviewerRemovalReadback(removedReviewerTails, options)") :
        candidate_helpers.index("function removeSelectedAssignedReviewers()")
    ]
    assert "invitation: reviewerAssignmentInvitationId()" in removal_readback
    assert "AUTO_ASSIGN_CONFIG.reviewersAssignmentId" not in removal_readback


def test_reviewer_assignment_page_sets_due_date_for_new_assignments_only():
    hub_source = HUB_SOURCE.read_text(encoding="utf-8")
    shared = (HUB_PARTS / "shared_helpers.py").read_text(encoding="utf-8")
    candidate_helpers = (HUB_PARTS / "candidate_data_helpers.py").read_text(encoding="utf-8")
    invite = (HUB_PARTS / "invite_new_reviewers_tab.py").read_text(encoding="utf-8")
    refresh_source = (
        REPO_ROOT
        / "site_config/python_scripts/invitations/venue/under_review/reviewer_assignment_invitation_refresh.py"
    ).read_text(encoding="utf-8")
    hub_refresh_process = HUB_REFRESH_PROCESS.read_text(encoding="utf-8")
    recruitment_process = (
        REPO_ROOT / "site_config/invitations/reviewers/assignment_recruitment/process_functions/process.py"
    ).read_text(encoding="utf-8")
    reviewer_console = (
        REPO_ROOT / "site_config/global_settings/reviewer_console_webfield.js"
    ).read_text(encoding="utf-8")
    payload_helper = shared[
        shared.index("function reviewerAssignmentEdgePayload(tail, actorSignature, edgeLabel)") :
        shared.index("function reviewerAssignmentErrorMessage(error, fallbackMessage)")
    ]

    assert "'reviewPeriodDays': int(journal.get_review_period_length(note) * 7)" in hub_source
    assert "auto_assign_config['reviewPeriodDays'] = int(journal.get_review_period_length(note) * 7)" in hub_source
    assert "journal.get_due_date(weeks=journal.get_reviewer_assignment_period_length())" in hub_refresh_process
    assert "function defaultReviewerDueDateInputValue()" in shared
    assert "var reviewPeriodDays = Number(AUTO_ASSIGN_CONFIG.reviewPeriodDays || 0);" in shared
    assert "function reviewerDueDateMillisFromInput(inputId)" in shared
    assert "Date.UTC(Number(parsed[1]), Number(parsed[2]) - 1, Number(parsed[3]))" in shared
    assert "new Date(value + 'T23:59:59.999')" not in shared
    assert "function reviewerDueDateMillisFromInput(inputId)" in shared
    assert "inputId = inputId || 'new-reviewer-due-date';" in shared
    assert "id=\\\"reviewer-assignment-due-date\\\"" not in hub_refresh_process
    assert "Review due date" in shared
    assert "function reviewerDueDateEdgePayload(tail, actorSignature, dueDateMillis)" in shared
    assert "invitation: AUTO_ASSIGN_CONFIG.reviewersReviewDueDateId" in shared
    assert "reviewerDueDateMillisFromInput('invite-reviewer-due-date')" in invite
    assert "review_duedate=review_due_date" in refresh_source
    assert "def invite_review_due_date_millis(invite_edge):" in recruitment_process
    assert "due_date = int_or_none(getattr(invite_edge, 'weight', None))" in recruitment_process
    assert "label='Review Due Date'" in recruitment_process
    assert "function reviewerAssignmentDueDateMillis(assignmentEdge, dueDateEdge)" in candidate_helpers
    assert "var storedDueDate = reviewerDueDateEdgeMillis(dueDateEdge)" in candidate_helpers
    assert "if (storedDueDate) return storedDueDate;" in candidate_helpers
    assert "return Number(assignmentEdge.cdate) + (Number(AUTO_ASSIGN_CONFIG.reviewPeriodDays) * 24 * 60 * 60 * 1000);" in candidate_helpers
    assert "Review Due Date</th>" in candidate_helpers
    assert "Change due date" not in candidate_helpers
    assert "var activeReviewerAssignmentEdgeForSubmission = function(assignmentEdges, submission)" in reviewer_console
    assert "assignmentEdges,\n      consoleProfileId" in reviewer_console
    assert "var activeReviewerDueDateEdgeForSubmission = function(dueDateEdges, submission)" in reviewer_console
    assert "if (dueDateEdge && dueDateEdge.weight) return Number(dueDateEdge.weight);" in reviewer_console
    assert "duedate: reviewerDueDateMillis(reviewerAssignmentEdge, reviewerDueDateEdge) || JMLRPermissionHelpers.getReviewerEffectiveDueDate(reviewInvitation)" in reviewer_console


def test_reviewer_assignment_refresh_replaces_stale_broad_child_edge_schema():
    refresh_source = (
        REPO_ROOT
        / "site_config/python_scripts/invitations/venue/under_review/reviewer_assignment_invitation_refresh.py"
    ).read_text(encoding="utf-8")

    assert "reviewer_assignment_id = journal.get_reviewer_assignment_id(number=note.number)" in refresh_source
    assert '"id": {"param": {"withInvitation": reviewer_assignment_id, "optional": True}}' in refresh_source
    assert '"head": {"param": {"type": "note", "const": note.id}}' in refresh_source
    assert '"ddate": {"param": {"range": [0, 9999999999999], "optional": True, "deletable": True}}' in refresh_source
    assert '"cdate": {"param": {"range": [0, 9999999999999], "optional": True, "deletable": True}}' in refresh_source
    assert '"tail": {' in refresh_source
    assert '"type": "profile"' in refresh_source
    assert '"options": {"group": journal.get_reviewers_id()}' in refresh_source
    assert '"label": {"param": {"optional": True, "deletable": True, "minLength": 1}}' in refresh_source
    assert '"writers": [' in refresh_source
    assert "journal.get_editors_in_chief_id()" in refresh_source
    assert "journal.get_action_editors_id(note.number)" in refresh_source
    assert '{"value": journal.venue_id, "optional": True}' in refresh_source
    assert '{"value": journal.get_editors_in_chief_id(), "optional": True}' in refresh_source
    assert '"prefix": f"{journal.venue_id}/Paper{note.number}/Action_Editor_",' in refresh_source
    assert 'reviewer_assignment_invitation.edge = reviewer_assignment_edge_schema' in refresh_source
    assert "reviewer_assignment_edge_schema['signatures'] = [journal.venue_id]" not in refresh_source
    assert "reviewer_assignment_edge_schema['writers'] = [journal.venue_id]" not in refresh_source
    assert '"tail": {"value": journal.get_reviewers_id()}' not in refresh_source


def test_backend_reviewer_assignment_state_prefers_paper_scoped_edges_with_legacy_fallback():
    reviewer_process = (
        REPO_ROOT / "site_config/invitations/reviewers/assignment/process_functions/process.py"
    ).read_text(encoding="utf-8")
    reviewer_sync = (
        REPO_ROOT / "site_config/python_scripts/invitations/venue/under_review/reviewer_sync.py"
    ).read_text(encoding="utf-8")
    paper_status = (
        REPO_ROOT / "site_config/python_scripts/invitations/venue/status/paper_status_refresh.py"
    ).read_text(encoding="utf-8")
    decision_refresh = (
        REPO_ROOT / "site_config/python_scripts/invitations/venue/under_review/decision_refresh.py"
    ).read_text(encoding="utf-8")

    for source in [reviewer_process, reviewer_sync, paper_status]:
        assert "journal.get_reviewer_assignment_id(number=" in source
        assert "journal.get_reviewer_assignment_id()" in source

    assert "exec(\"{{PYTHON_SCRIPT_JSON:invitations/venue/reviewer_assignment_edges.py}}\", reviewer_assignment_edges_namespace)" in reviewer_process
    assert "reviewer_assignment_edges_namespace['reviewer_assignment_edges_for_submission'](" in reviewer_process
    assert "journal.get_reviewer_assignment_id(number=submission.number),\n        journal.get_reviewer_assignment_id()" in reviewer_sync
    assert "edge.tail in tails" in reviewer_sync
    assert "seen_reviewer_tails = set()" in paper_status
    assert "journal.get_reviewer_assignment_id(number=paper_number),\n        journal.get_reviewer_assignment_id()" in paper_status
    assert "resubmission_reviewer_auto_assignment" in decision_refresh


def test_reviewer_due_date_helper_prefers_edge_stored_due_date():
    helper = (
        REPO_ROOT / "site_config/python_scripts/invitations/venue/review/review_due_date_helpers.py"
    ).read_text(encoding="utf-8")

    assert "stored_due_date = _int_or_none(reviewer_due_date)" in helper
    assert "if stored_due_date is not None:" in helper
    assert "assigned_at = _int_or_none(edge_time_millis(edge))" in helper


def test_eic_previous_reviewer_continuity_posts_only_paper_scoped_reviewer_edges():
    eic_tables = (
        REPO_ROOT / "site_config/global_settings/eic_console_webfield_parts/40_paper_tables.js"
    ).read_text(encoding="utf-8")
    ae_process = (
        REPO_ROOT / "site_config/invitations/action_editors/assignment/process_functions/process.py"
    ).read_text(encoding="utf-8")

    post_function = eic_tables[
        eic_tables.index("var postPreviousContinuityAssignmentRequest = function") :
        eic_tables.index("var previousContinuityActionEditorAlreadyAssigned = function")
    ]
    readback_function = eic_tables[
        eic_tables.index("var waitForPreviousContinuityAssignmentReadback = function") :
        eic_tables.index("var loadPreviousContinuityCurrentState = function")
    ]

    assert "invitation: VENUE_ID + '/-/Previous_Continuity_Assignment'" in post_function
    assert "paper_number: { value: submission.number }" in post_function
    assert "Webfield2.api.post('/notes/edits?awaitProcess=true', {" in post_function
    assert "var reviewerAssignmentId = VENUE_ID + '/Paper' + submission.number + '/Reviewers/-/Assignment';" in readback_function
    assert "VENUE_ID + '/Reviewers/-/Assignment'" not in readback_function

    ae_previous_reviewer_post_function = ae_process[
        ae_process.index("def reviewer_assignment_invitation_for_post(submission):") :
        ae_process.index("def post_selected_previous_reviewer_assignments(submission):")
    ]
    assert "return journal.get_reviewer_assignment_id(number=submission.number)" in ae_previous_reviewer_post_function
    assert "return journal.get_reviewer_assignment_id()" not in ae_previous_reviewer_post_function
    assert "client.get_invitation(journal.get_reviewer_assignment_id(number=submission.number))" not in ae_previous_reviewer_post_function
    assert "invitation=reviewer_assignment_invitation_for_post(refreshed_submission)" in ae_process


def test_checked_reviewer_process_does_not_repost_current_edges_to_legacy_assignment_invitation():
    reviewer_process = (
        REPO_ROOT / "site_config/invitations/reviewers/assignment/process_functions/process.py"
    ).read_text(encoding="utf-8")

    assert "assignment_invitation_id = getattr(edge, 'invitation', None) or getattr(invitation, 'id', None) or journal.get_reviewer_assignment_id()" in reviewer_process
    assert "paper_assignment_invitation_id = journal.get_reviewer_assignment_id(number=note.number)" in reviewer_process
    assert "active_assignment_edges_for_submission" in reviewer_process
    assert "store_reviewer_assignment_due_date(edge)" in reviewer_process
    assert "due_date_edge = active_reviewer_due_date_edge(assignment_edge)" in reviewer_process
    assert "stored_due_date = int_or_none(getattr(due_date_edge, 'weight', None))" in reviewer_process
    assert "stored_due_date = int_or_none(getattr(assignment_edge, 'duedate', None))" in reviewer_process
    assert "if stored_due_date is not None:" in reviewer_process
    assert "return int(stored_due_date)" in reviewer_process
    assert "reviewer_assignment_due_date = assignment_cdate + int(review_period_length * 7 * 24 * 60 * 60 * 1000)" in reviewer_process
    assert "invitation=reviewer_due_date_edge_invitation_id()" in reviewer_process
    assert "reviewer_assignment_due_date_millis = store_reviewer_assignment_due_date(edge)" in reviewer_process
    assert "reviewer_assignment_due_date = datetime.datetime.fromtimestamp(reviewer_assignment_due_date_millis / 1000)" in reviewer_process
    assert 'review_duedate=reviewer_assignment_due_date.strftime("%b %d")' in reviewer_process
    for post_block in reviewer_process.split("client.post_edge(openreview.api.Edge(")[1:]:
        block = post_block.split("))", 1)[0]
        assert "invitation=journal.get_reviewer_assignment_id()" not in block


def test_remove_reviewer_uses_assignment_hub_checked_edges():
    candidate_helpers = (HUB_PARTS / "candidate_data_helpers.py").read_text(encoding="utf-8")
    reviewer_process = (
        REPO_ROOT / "site_config/invitations/reviewers/assignment/process_functions/process.py"
    ).read_text(encoding="utf-8")

    assert not (REPO_ROOT / "site_config/python_scripts/invitations/venue/under_review/remove_reviewer.py").exists()
    assert "function removeSelectedAssignedReviewers()" in candidate_helpers
    assert 'class="remove-assigned-reviewer"' in candidate_helpers
    assert "Webfield2.api.post('/edges?awaitProcess=true', payload)" in candidate_helpers
    assert "ddate: Date.now()" in candidate_helpers
    assert "waitForReviewerRemovalReadback(selectedAssignments.map(function(assignment) { return assignment.reviewer; }), {" in candidate_helpers
    assert "reviewer_sync_namespace['sync_remove_paper_reviewer'](client, journal, note, edge.tail)" in reviewer_process


def test_reviewer_assignment_invitation_allows_checked_ae_and_eic_submission():
    edge = json.loads(ASSIGNMENT_EDGE.read_text(encoding="utf-8"))

    assert edge["writers"] == [
        "JMLR/Editors_In_Chief",
        "JMLR/Paper${{2/head}/number}/Action_Editors",
    ]
    signature_items = edge["signatures"]["param"]["items"]
    assert {"value": "JMLR", "optional": True} in signature_items
    assert {"value": "JMLR/Editors_In_Chief", "optional": True} in signature_items
    assert {
        "prefix": "JMLR/Paper${{3/head}/number}/Action_Editor_",
        "optional": True,
    } in signature_items


def test_openreview_conflict_override_does_not_bypass_hard_reviewer_blockers():
    shared = (HUB_PARTS / "shared_helpers.py").read_text(encoding="utf-8")
    candidate_helpers = (HUB_PARTS / "candidate_data_helpers.py").read_text(encoding="utf-8")
    search = (HUB_PARTS / "search_reviewers_tab.py").read_text(encoding="utf-8")
    auto = (HUB_PARTS / "auto_assign_reviewers_tab.py").read_text(encoding="utf-8")

    assert "if (candidate.cooldownBlocked) candidate.blockers.push({ code: 'cooldown'" in candidate_helpers
    assert "statusLabel: reviewerCandidateStatusLabel(candidate)" in candidate_helpers
    assert "blockerCodes: blockerCodes" in candidate_helpers
    assert "overrideAllowed: reviewerCandidateOverrideAllowed(candidate)" in candidate_helpers
    assert "if (candidate.cooldownBlocked) blockers.push({ code: 'cooldown'" in shared
    assert "if (candidate.active === false) blockers.push({ code: 'not_reviewer_member'" in shared
    assert "var cooldownMillis = Number(AUTO_ASSIGN_CONFIG.reviewerNewAssignmentCooldownDays || 0) * 24 * 60 * 60 * 1000;" in shared
    assert "edge.head !== AUTO_ASSIGN_CONFIG.noteId && edge.cdate && edge.cdate >= cutoff" in shared
    assert "until = latestRecentAssignment ? latestRecentAssignment.cdate + cooldownMillis : null;" in shared
    assert "var severity = eligible ? 'eligible' : (unavailable ? 'unavailable' : (blockers.length ? 'blocked' : (openreviewConflict ? 'warning_conflict' : 'blocked')));" in shared
    assert "overridable: openreviewConflict && !unavailable && !blockers.length" in shared
    assert "selectable: !unavailable && !blockers.length" in shared
    assert "function reviewerCandidateRowAttributes(candidate, overrideChecked)" in shared
    assert "data-reviewer-eligibility" in shared
    assert "data-reviewer-status" in shared
    assert "data-reviewer-selectable" in shared
    assert "data-reviewer-override-allowed" in shared
    assert "function reviewerCandidateEffectivelySelectable(candidate, overrideChecked)" in shared
    assert "function reviewerCandidateOverrideAllowed(candidate)" in shared
    assert "return classification.severity === 'warning_conflict'" in shared
    assert "labels.map(function(label) { return '<li>' + escapeAutoAssignHtml(label) + '</li>'; }).join('')" in shared
    assert "classification.blockers || []).forEach(function(blocker)" in shared
    assert "return actorSignature === AUTO_ASSIGN_CONFIG.venueId + '/Editors_In_Chief'" in shared
    assert "Rating/timeliness history unavailable" in shared

    assert "reviewerCandidateEffectivelySelectable(candidate, conflictOverrideChecked)" in search
    assert "reviewerCandidateRowAttributes(candidate, conflictOverrideChecked)" in search
    assert "return reviewerCandidateOverrideAllowed(candidate);" in search
    assert "active: true" in search
    assert "var isOpenReviewConflict = candidate.classification && candidate.classification.severity === 'warning_conflict';" in search
    assert "var isOpenReviewConflict = candidate.classification && candidate.classification.severity === 'warning_conflict';" in auto
    assert "var activeReviewerTailSet = new Set(reviewerCandidateTails || []);" in auto
    assert "active: activeReviewerTailSet.has(tail)" in auto
    assert "reviewerCandidateEffectivelySelectable(candidate, conflictOverrideChecked)" in auto
    assert "reviewerCandidateRowAttributes(candidate, conflictOverrideChecked)" in auto


def test_reviewer_assignment_surfaces_keep_hard_author_conflicts_unselectable():
    shared = (HUB_PARTS / "shared_helpers.py").read_text(encoding="utf-8")
    candidate_helpers = (HUB_PARTS / "candidate_data_helpers.py").read_text(encoding="utf-8")
    search = (HUB_PARTS / "search_reviewers_tab.py").read_text(encoding="utf-8")
    auto = (HUB_PARTS / "auto_assign_reviewers_tab.py").read_text(encoding="utf-8")
    hub_source = HUB_SOURCE.read_text(encoding="utf-8")
    preprocess = PREPROCESS.read_text(encoding="utf-8")

    assert "'submissionAuthorList': note.content.get('author_list', {}).get('value', '')" in hub_source
    assert "'submissionConflictOfInterests': note.content.get('conflict_of_interests', {}).get('value', '')" in hub_source
    assert "author_list: AUTO_ASSIGN_CONFIG.submissionAuthorList || ''" in shared
    assert "conflict_of_interests: AUTO_ASSIGN_CONFIG.submissionConflictOfInterests || ''" in shared
    assert "return JMLRPermissionHelpers.classifyAssignmentCandidate(" in shared
    assert "{ role: 'reviewer' }" in shared
    assert "if (classification.conflict && classification.conflict.kind === 'author_conflict') codes.push('hard_conflict');" in shared
    assert "return classification.severity === 'warning_conflict'" in shared
    assert "return code !== 'openreview_conflict';" in shared
    assert "' data-reviewer-selectable=\"' + (selectable ? 'true' : 'false') + '\"'" in shared
    assert "' data-reviewer-hard-conflict=\"' + (blockerCodes.indexOf('hard_conflict') >= 0 ? 'true' : 'false') + '\"'" in shared
    assert "enabled: !!candidate.classification.eligible" in candidate_helpers
    assert "overrideAllowed: reviewerCandidateOverrideAllowed(candidate)" in candidate_helpers

    assert "reviewerCandidateEffectivelySelectable(candidate, conflictOverrideChecked)" in search
    assert "reviewerCandidateRowAttributes(candidate, conflictOverrideChecked)" in search
    assert "refreshReviewerSearchCandidateConflict(selectedCandidate, signature)" in search
    assert "materializeOnDemandReviewerConflict(candidate.tail, actorSignature)" in search
    assert "postCheckedReviewerAssignmentEdge(tail, signature, reviewerAssignmentOverrideLabel(refreshedCandidate, signature), selectedDueDateMillis)" in search
    assert "reviewerCandidateEffectivelySelectable(candidate, conflictOverrideChecked)" in auto
    assert "reviewerCandidateRowAttributes(candidate, conflictOverrideChecked)" in auto
    assert "var selectedTails = $('.auto-assign-selectable:checked:not(:disabled)').map(function() { return $(this).val(); }).get();" in auto
    assert "postCheckedReviewerAssignmentEdge(candidate.tail, signature, reviewerAssignmentOverrideLabel(candidate, signature), selectedDueDateMillis)" in auto

    assert "hard_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, edge.tail)" in preprocess
    assert "if hard_conflict:" in preprocess
    assert "openreview_conflict = assignment_conflict_namespace['get_assignment_conflict'](client, journal, submission, edge.tail, conflict_type='openreview')" in preprocess
    assert "edge.label in [ae_openreview_conflict_override_label, eic_openreview_conflict_override_label]" in preprocess


def test_existing_reviewer_assignment_hub_refresh_rewrites_note_derived_config_fields():
    hub_source = HUB_SOURCE.read_text(encoding="utf-8")
    refresh_branch = hub_source[hub_source.index("if config_start >= 0:") :]

    for assignment in [
        "auto_assign_config['noteId'] = note.id",
        "auto_assign_config['paperNumber'] = note.number",
        "auto_assign_config['submissionTitle'] = note.content['title']['value']",
        "auto_assign_config['submissionAbstract'] = note.content.get('abstract', {}).get('value', '')",
        "auto_assign_config['submissionCoverLetter'] = note.content.get('cover_letter', {}).get('value', '')",
        "auto_assign_config['submissionAuthorList'] = note.content.get('author_list', {}).get('value', '')",
        "auto_assign_config['submissionConflictOfInterests'] = note.content.get('conflict_of_interests', {}).get('value', '')",
        "auto_assign_config['paperPdfUrl'] = f'/pdf?id={note.id}'",
        "auto_assign_config['submissionAuthorIds'] = note.content.get('authorids', {}).get('value') or []",
        "auto_assign_config['reviewersInviteAssignmentId'] = reviewer_invite_assignment_id",
        "auto_assign_config['assignedActionEditorSignature'] = assigned_action_editor_signature",
    ]:
        assert assignment in refresh_branch

    assert refresh_branch.index("auto_assign_config['submissionConflictOfInterests']") < refresh_branch.index(
        "web[:config_value_start]"
    )
