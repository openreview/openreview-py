from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OVERLAY = (
    REPO_ROOT
    / "site_config"
    / "python_scripts"
    / "invitations"
    / "venue"
    / "submission"
    / "paper_action_editor_assignment_overlay.py"
)
WEBFIELD_PARTS = REPO_ROOT / "site_config" / "global_settings" / "assign_action_editor_webfield_parts"


def test_action_editor_assignment_browser_contract_names_sources_and_submit_uses_contract_invitation():
    overlay = OVERLAY.read_text(encoding="utf-8")
    constants = (WEBFIELD_PARTS / "00_constants.js").read_text(encoding="utf-8")
    helpers = (WEBFIELD_PARTS / "10_shared_helpers.js").read_text(encoding="utf-8")
    data_loading = (WEBFIELD_PARTS / "20_data_loading.js").read_text(encoding="utf-8")
    assignment_ui = (WEBFIELD_PARTS / "90_assign_action_editor.js").read_text(encoding="utf-8")
    submit_helper = assignment_ui[
        assignment_ui.index("var postSelectedActionEditorAssignment = function(") :
        assignment_ui.index("var parsePreviousSubmissionForumId = function(")
    ]

    assert "def action_editor_assignment_browser_contract(" in overlay
    assert '"assignment_invitation": assignment_invitation_id' in overlay
    assert '"deployed_assignment_sources": [\n            assignment_invitation_id,' in overlay
    assert '"readback_assignment_sources": [\n            assignment_invitation_id,' in overlay
    assert "reviewer_assignment_id = getattr(" in overlay
    assert '"reviewer_assignment_invitation": reviewer_assignment_id' in overlay
    assert "Modify_Reviewer_Assignments" not in overlay
    assert '"paper_reviewers_group": paper_reviewers_id' in overlay
    assert '"affinity_score_invitation": ae_affinity_id' in overlay
    assert '"openreview_conflict_invitation": ae_conflict_id' in overlay
    assert '"candidate_refresh_invitation": f"{venue_id}/-/Action_Editor_Candidate_Conflict_Refresh"' in overlay
    assert '"action_editor_availability_invitation": ae_availability_id' in overlay
    assert '"custom_max_papers_invitation": action_editors_id + "/-/Custom_Max_Papers"' in overlay
    assert '"assignment_history_sources": [' in overlay
    assert "journal.get_ae_assignment_id(archived=True)" in overlay
    assert '"raw_edges_browse_default": False' in overlay
    assert "assignment_browser_contract = action_editor_assignment_browser_contract(" in overlay
    assert '"web": build_paper_action_editor_assignment_web(note, assignment_invitation_id, assignment_browser_contract)' in overlay
    assert "var ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT = {json.dumps(assignment_browser_contract)};" in overlay

    assert "var ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT = typeof ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT !== 'undefined'" in constants
    assert "var actionEditorAssignmentBrowserContract = function()" in helpers
    assert "var actionEditorAssignmentInvitationId = function()" in helpers
    assert "return actionEditorAssignmentBrowserContract().assignment_invitation || PAPER_ACTION_EDITORS_ASSIGNMENT_ID;" in helpers
    assert "var actionEditorAssignmentReadbackSources = function()" in helpers
    assert "var actionEditorReviewerEntrySources = function(submission)" in helpers
    assert "var actionEditorAssignmentScoreSources = function()" in helpers
    assert "var actionEditorAssignmentConflictSources = function()" in helpers
    assert "var actionEditorAssignmentAvailabilitySources = function()" in helpers
    assert "var actionEditorAssignmentLoadSources = function()" in helpers

    assert "invitation: actionEditorAssignmentInvitationId()" in submit_helper
    assert "invitation: PAPER_ACTION_EDITORS_ASSIGNMENT_ID" not in submit_helper
    assert "waitForActionEditorAssignmentReadback(submission, selectedTail, Date.now())" in submit_helper
    assert "var reviewerEntrySources = actionEditorReviewerEntrySources(submission);" in assignment_ui
    assert "conflictSources.candidateRefreshInvitation" in assignment_ui
    assert "getEdgesByTailMap(conflictSources.openreviewConflictInvitation, headId)" in data_loading
    assert "getEdgesByTailMap(conflictSources.reviewerConflictInvitation, headId)" in data_loading


def test_action_editor_assignment_submit_remove_readback_and_sources_use_contract_helpers():
    helpers = (WEBFIELD_PARTS / "10_shared_helpers.js").read_text(encoding="utf-8")
    data_loading = (WEBFIELD_PARTS / "20_data_loading.js").read_text(encoding="utf-8")
    assignment_ui = (WEBFIELD_PARTS / "90_assign_action_editor.js").read_text(encoding="utf-8")

    readback_helper = assignment_ui[
        assignment_ui.index("var getActionEditorAssignmentReadbackEdges = function(submission)") :
        assignment_ui.index("var reviewerEntryInvitationReadback = function(invitationId)")
    ]
    wait_helper = assignment_ui[
        assignment_ui.index("var waitForActionEditorAssignmentReadback = function(submission, selectedTail, startedAt)") :
        assignment_ui.index("var removeActionEditorGroupMember = function(submission, actionEditorId)")
    ]
    group_removal_helper = assignment_ui[
        assignment_ui.index("var removeActionEditorGroupMember = function(submission, actionEditorId)") :
        assignment_ui.index("var postActionEditorAssignmentRemovalEdge = function(assignmentEdge)")
    ]
    edge_delete_helper = assignment_ui[
        assignment_ui.index("var postActionEditorAssignmentRemovalEdge = function(assignmentEdge)") :
        assignment_ui.index("var postCurrentActionEditorRemoval = function(")
    ]
    remove_helper = assignment_ui[
        assignment_ui.index("var postCurrentActionEditorRemoval = function(submission, assignedAe, assignmentEdge, statusElement, buttonElement)") :
        assignment_ui.index("var postSelectedActionEditorAssignment = function(")
    ]
    submit_helper = assignment_ui[
        assignment_ui.index("var postSelectedActionEditorAssignment = function(") :
        assignment_ui.index("var parsePreviousSubmissionForumId = function(")
    ]

    assert "var actionEditorAssignmentContractSection = function(sectionName)" in helpers
    assert "var actionEditorAssignmentReadbackSources = function()" in helpers
    assert "var sources = actionEditorAssignmentBrowserContract().readback_assignment_sources;" in helpers
    assert "return [actionEditorAssignmentInvitationId()].filter(Boolean);" in helpers
    assert "var actionEditorReviewerEntrySources = function(submission)" in helpers
    assert "var sources = actionEditorAssignmentContractSection('reviewer_entry_sources');" in helpers
    assert "var actionEditorAssignmentScoreSources = function()" in helpers
    assert "var actionEditorAssignmentConflictSources = function()" in helpers
    assert "var actionEditorAssignmentAvailabilitySources = function()" in helpers
    assert "var actionEditorAssignmentLoadSources = function()" in helpers

    assert "var sources = actionEditorAssignmentReadbackSources();" in readback_helper
    assert "invitation: sourceId" in readback_helper
    assert "actionEditorAssignmentInvitationId()" not in readback_helper
    assert "PAPER_ACTION_EDITORS_ASSIGNMENT_ID" not in readback_helper

    assert "var reviewerEntrySources = actionEditorReviewerEntrySources(submission);" in wait_helper
    assert "getActionEditorAssignmentReadbackEdges(submission)" in wait_helper
    assert "reviewerEntrySources.reviewerAssignmentInvitation" in wait_helper
    assert "reviewerEntrySources.modifyReviewerAssignmentsInvitation" not in wait_helper
    assert "reviewerEntrySources.paperReviewersGroup" in wait_helper
    assert "PAPER_ACTION_EDITORS_ASSIGNMENT_ID" not in wait_helper

    assert "invitation: assignmentEdge.invitation || actionEditorAssignmentInvitationId()" in edge_delete_helper
    assert "id: assignmentEdge.id" in edge_delete_helper
    assert "ddate: Date.now()" in edge_delete_helper
    assert "Webfield2.api.post('/edges?awaitProcess=true', removalBody)" in edge_delete_helper
    assert "postActionEditorAssignmentRemovalEdge(assignmentEdge).then(function() {" in remove_helper
    assert "prefix: VENUE_ID + '/Paper' + submission.number + '/Action_Editor_'" in group_removal_helper
    assert "member: actionEditorId" in group_removal_helper
    assert "var anonMembersToRemove = anonGroupIds.filter(function(anonGroupId) {" in group_removal_helper
    assert "return members.indexOf(anonGroupId) >= 0;" in group_removal_helper
    assert "var membersToRemove = anonMembersToRemove.length ? anonMembersToRemove : (members.indexOf(actionEditorId) >= 0 ? [actionEditorId] : []);" in group_removal_helper
    assert "if (!membersToRemove.length) {" in group_removal_helper
    assert "remove: _.uniq(membersToRemove)" in group_removal_helper
    assert "invitation: PAPER_ACTION_EDITORS_ASSIGNMENT_ID" not in remove_helper

    assert "invitation: actionEditorAssignmentInvitationId()" in submit_helper
    assert "waitForActionEditorAssignmentReadback(submission, selectedTail, Date.now())" in submit_helper
    assert "invitation: PAPER_ACTION_EDITORS_ASSIGNMENT_ID" not in submit_helper

    assert "var conflictSources = actionEditorAssignmentConflictSources();" in data_loading
    assert "var availabilitySources = actionEditorAssignmentAvailabilitySources();" in data_loading
    assert "actionEditorAssignmentScoreSources().affinityScoreInvitation" in assignment_ui
    assert "actionEditorAssignmentScoreSources().matchingInputGroup" in assignment_ui
    assert "actionEditorAssignmentAvailabilitySources().actionEditorAvailabilityInvitation" in assignment_ui
    assert "actionEditorAssignmentLoadSources().assignmentHistorySources" in assignment_ui
    assert "actionEditorAssignmentLoadSources().customMaxPapersInvitation" in assignment_ui
    for stale_source in [
        "invitation: ACTION_EDITORS_AFFINITY_SCORE_ID",
        "invitation: ACTION_EDITORS_CONFLICT_ID",
        "invitation: ACTION_EDITORS_AVAILABILITY_ID",
        "invitation: ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID",
        "invitation: PAPER_ACTION_EDITORS_ASSIGNMENT_ID",
    ]:
        assert stale_source not in data_loading
        assert stale_source not in assignment_ui
