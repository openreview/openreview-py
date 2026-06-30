var renderData = function(venueStatusData) {
  renderActionEditorConsoleControlsIntro('#invitation');

  if (venueStatusData.availabilityInvitation && venueStatusData.consoleProfileId) {
    renderAvailabilityForm('#invitation', {
      invitationId: ACTION_EDITOR_ID + '/-/' + AVAILABILITY_NAME,
      headId: ACTION_EDITOR_ID,
      tailId: venueStatusData.consoleProfileId,
      edgeId: venueStatusData.availabilityEdge && venueStatusData.availabilityEdge.id,
      edge: venueStatusData.availabilityEdge
    });
  }

  renderExpertiseSelectionLink('#invitation');
  renderResubmissionPolicy('#invitation');

  var renderPaperTable = function(container, rows) {
  Webfield2.ui.renderTable(container, rows, {
    headings: ['#', 'Paper Summary', 'Review Progress', 'Decision Status'],
    renders: [
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      function(data) {
        var noteSummary = Handlebars.templates.noteSummary(data);
        var beyondPdfTag = data.beyondPdf ? '<span class="badge" style="background-color: #3f6978">Beyond PDF</span>' : '';
        return noteSummary + beyondPdfTag + renderPreviousSubmissionLink(data) + renderJmlrSubmissionDetails(data);
      },
      Handlebars.templates.noteReviewers,
      function(data) {
        var html = Handlebars.templates.noteMetaReviewStatus(data);
        return isAcceptedDecisionRecommendation(data && data.recommendation) ? html.replace(/<a\b[^>]*>\s*Read\s*<\/a>/g, '') : html;
      }
    ],
    extraClasses: 'console-table paper-table',
    postRenderTable: function() {
      $('.console-table th').eq(0).css('width', '4%');  // #
      $('.console-table th').eq(1).css('width', '36%'); // Paper Summary
      $('.console-table th').eq(2).css('width', '30%'); // Review Progress
      $('.console-table th').eq(3).css('width', '30%'); // Action Editor Decision
    }
  });
  };

  // Paper Tabs
  renderPaperTable('#active-papers', venueStatusData.activeRows);
  renderPaperTable('#assigned-papers', venueStatusData.rows);

  // Pending Tasks Tab
  renderPendingTasks('#pending-tasks', venueStatusData.invitations);

};

main();
