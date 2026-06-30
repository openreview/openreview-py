var renderData = function(venueStatusData) {
  renderRoleStatisticsTab(venueStatusData.journalStats);

  renderPendingTasksList('#pending-tasks', venueStatusData.pendingTaskRows);
  renderTable('active-papers', venueStatusData.activeStatusRows);
  renderTable('camera-ready', venueStatusData.cameraReadyStatusRows);
  renderTable('decision-made', venueStatusData.decisionMadeStatusRows);
  renderTable('all-submissions', venueStatusData.submissionStatusRows);
  renderActionEditorStatusTable('#action-editor-status', venueStatusData.actionEditorStatusRows);
  renderReviewerStatusTable('#reviewer-status', venueStatusData.reviewerStatusRows);
  renderBulkInviteTab(venueStatusData);
  renderAssignRolesTab(venueStatusData);
};

main();
