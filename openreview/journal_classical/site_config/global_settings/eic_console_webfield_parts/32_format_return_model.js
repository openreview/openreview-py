    ];
    var previousSubmissionUrl = getPreviousSubmissionUrl(submission);
    if (previousSubmissionUrl) {
      aeActions.push({
        name: 'Previous JMLR Submission',
        url: previousSubmissionUrl
      })
    }

    paperStatusRows.push({
      checked: { noteId: submission.id, checked: false },
      submissionNumber: { number: parseInt(number, 10) },
      submission: formattedSubmission,
      assignmentSetupData: assignmentSetupData,
      reviewProgressData: {
        requiredReviewers: requiredReviewerCountForSubmission(submission),
        noteId: submission.id,
        paperNumber: number,
        numSubmittedReviews: reviews.length,
        numReviewers: paperReviewers.length,
        reviewers: paperReviewerStatus,
        reviewerSearchData: Object.values(paperReviewerStatus).map(function(reviewer) {
          return [
            reviewer.id,
            reviewer.name,
            reviewer.email
          ].filter(Boolean).join(' ');
        }),
        expandReviewerList: true,
        sendReminder: true,
        showPreferredEmail: PREFERRED_EMAILS_ID,
        referrer: referrerUrl,
        actions: ([UNDER_REVIEW_STATUS].includes(submission.content.venueid.value) && reviewerAssignmentInvitation) ? [
          {
            name: 'Edit Assignments',
            url: '/invitation?id=' + encodeURIComponent(VENUE_ID + '/Paper' + number + '/Reviewers/-/Assignment') +
              '&referrer=' + encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + '#assigned-papers)')
          }
        ] : [],
        duedate: JMLRPermissionHelpers.getReviewerEffectiveDueDate(reviewInvitation)
      },
      actionEditorProgressData: {
        recommendation: metaReview && metaReview.content.recommendation,
        status: {
          Certification: metaReview ? metaReview.content.certification.join(', ') : ''
        },
        numMetaReview: metaReview ? 'One' : 'No',
        areachair: !actionEditor.name ? { name: 'No Action Editor' } : { id: actionEditor.id, name: actionEditor.name },
        actionEditor: actionEditor,
        actionEditorAssignmentEdge: (actionEditorAssignmentEdgesByHead[submission.id] || []).find(function(edge) {
          return actionEditor.id && actionEditor.id !== 'No Action Editor' ? edge.tail === actionEditor.id : edge && !edge.ddate && edge.tail;
        }) || activeActionEditorAssignmentEdge,
        metaReview: metaReview,
        referrer: referrerUrl,
        reviewPending: reviewInvitation && reviewNotes.length < requiredReviewerCountForSubmission(submission),
        recommendationPending: false,
        ratingPending: reviewerRatingInvitations.length && reviewerRatingReplies.length < reviewNotes.length,
        decisionPending: decisionInvitation && decisionNotes.length == 0,
        decisionApprovalPending: metaReview && decisionApprovalNotes.length == 0,
        cameraReadyPending: (cameraReadyTask && !cameraReadyTask.complete) || (cameraReadyVerificationTask && !cameraReadyVerificationTask.complete),
        earlylateTaskDueDate: earlylateTaskDueDate,
        metaReviewName: 'Decision',
        committeeName: 'Action Editor',
        actions: aeActions,
        previousContinuity: previousContinuity,
        tableWidth: '100%',
        showPreferredEmail: PREFERRED_EMAILS_ID,
      },
      tasks: { invitations: tasks, forumId: submission.id },
      eicComments: {
        comments: submission.details.replies.filter(function(r) {
          return r.readers.length == 1 && r.readers[0] == EDITORS_IN_CHIEF_ID;
        }).sort(function(a, b) {
          return a.tcdate - b.tcdate;
        })
      },
      status: paperStatus
    });
  });

  var submittedStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === SUBMITTED_STATUS
    || row.submission.content.venueid === ASSIGNING_AE_STATUS
    || row.submission.content.venueid === ASSIGNED_AE_STATUS;
  });
  var rowHasHandlingActionEditor = function(row) {
    var progress = row.actionEditorProgressData || {};
    var assignedActionEditor = progress.actionEditor;
    if (assignedActionEditor && assignedActionEditor.id && assignedActionEditor.id !== 'No Action Editor') return true;
    return Boolean(progress.actionEditorAssignmentEdge && !progress.actionEditorAssignmentEdge.ddate && progress.actionEditorAssignmentEdge.tail);
  };
  var pendingTaskRows = submittedStatusRows.filter(function(row) {
    return !rowHasHandlingActionEditor(row);
  });
  var underReviewStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === UNDER_REVIEW_STATUS;
  });
  var underDiscussionStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === UNDER_REVIEW_STATUS
      && row.actionEditorProgressData.recommendationPending;
  });
  var underDecisionStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === UNDER_REVIEW_STATUS
      && (row.actionEditorProgressData.ratingPending || row.actionEditorProgressData.decisionPending || row.actionEditorProgressData.decisionApprovalPending);
  });
  var decisionPendingStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === DECISION_PENDING_STATUS
      && row.actionEditorProgressData.decisionApprovalPending;
  });
  var rowIds = {};
  var activeStatusRows = submittedStatusRows.concat(underReviewStatusRows, decisionPendingStatusRows).filter(function(row) {
    if (rowIds[row.submission.id]) {
      return false;
    }
    rowIds[row.submission.id] = true;
    return true;
  });
  var cameraReadyStatusRows = paperStatusRows.filter(function(row) {
    return [
      CAMERA_READY_REVISION_PENDING_STATUS,
      CAMERA_READY_CHECK_PENDING_STATUS,
      CAMERA_READY_APPROVED_STATUS,
      CAMERA_READY_PUBLISHED_STATUS,
      PUBLICATION_RETRACTED_STATUS
    ].includes(row.submission.content.venueid)
      || (
        row.submission.content.venueid === DECISION_PENDING_STATUS
        && row.actionEditorProgressData.cameraReadyPending
      );
  });
  var submissionStatusRows = paperStatusRows;
  var acceptedStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === VENUE_ID;
  });  

  var retractedStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === RETRACTED_STATUS;
  });
  var rejectedStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === REJECTED_STATUS;
  });
  var decisionMadeStatusRows = acceptedStatusRows.concat(rejectedStatusRows);

  // Generate journal stats for the role statistics tab
  var journalStats = {
    numReviewers: reviewers.members.length,
    numActionEditors: actionEditors.members.length,
    numExpertReviewers: (expertReviewers.members || []).length,
    numPendingTasks: pendingTaskRows.length,
    numActive: activeStatusRows.length,
    numSubmitted: submittedStatusRows.length,
    numUnderReview: underReviewStatusRows.length,
    numUnderDiscussion: underDiscussionStatusRows.length,
    numUnderDecision: underDecisionStatusRows.length,
    numDecisionMade: decisionMadeStatusRows.length,
    numAccepted: acceptedStatusRows.length,
    numRetracted: retractedStatusRows.length,
    numRejected: rejectedStatusRows.length,
    superInvitationIds: superInvitationIds,
    reviewerInvitationIds: reviewerInvitationIds.filter(function(inv) {
      return !inv.id.match(/\/-\/[^/]+\/Responsibility\//);
    }),
    aeInvitationIds: aeInvitationIds,
    activeAuthors: _.sortBy(
      _.toPairs(authorSubmissionsCount),
      function(pair) { return pair[1]; }
    ).reverse().slice(0, 20),
    incompleteEicTasks: incompleteEicTasks.sort(
      function(a, b) { return a[1].duedate - b[1].duedate; }
    ),
    overdueTasks: overdueTasks.sort(
      function(a, b) { return a[1].duedate - b[1].duedate; }
    ).slice(0, 20),
  };

  var reviewerRows = Object.values(reviewerStatusById);
  var actionEditorRows = Object.values(actionEditorStatusById);
  var memberId = function(member) {
    return typeof member === 'string' ? member : member.id;
  };
  var actionEditorMemberIds = actionEditors.members.map(memberId).filter(Boolean);
  var ossActionEditorMemberIds = ossActionEditors.members.map(memberId).filter(Boolean);
  var reviewerMemberIds = reviewers.members.map(memberId).filter(Boolean);
  var productionEditorMemberIds = productionEditors.members.map(memberId).filter(Boolean);
  var editorInChiefMemberIds = editorsInChiefGroup.members.map(memberId).filter(Boolean);
  var toReviewerStatusRow = function(row) {
    return {
      index: row.index,
      summary: row.summary,
      reviewerProgressData: row.reviewerProgressData,
      ratingData: row.ratingData,
      statusData: row.summary.status
    };
  };
  var toActionEditorStatusRow = function(row) {
    return {
      index: row.index,
      summary: row.summary,
      availabilityData: row.availabilityData,
      reviewProgressData: Object.assign({}, row.reviewProgressData, {
        numCompletedMetaReviews: row.decisionProgressData.numCompletedMetaReviews
      }),
      decisionTimingData: row.decisionTimingData,
      statusData: row.summary.status
    };
  };
  var toAvailabilityRow = function(row) {
    return {
      index: row.index,
      summary: row.summary,
      availabilityData: row.availabilityData
    };
  };
  var roleAssignmentRowsById = {};
  var ensureRoleAssignmentRow = function(summary) {
    if (!summary || !summary.id) return null;
    if (!roleAssignmentRowsById[summary.id]) {
      roleAssignmentRowsById[summary.id] = {
        index: { number: Object.keys(roleAssignmentRowsById).length + 1 },
        summary: summary,
        roleAssignmentData: {
          profileId: summary.id,
          isActionEditor: actionEditorMemberIds.includes(summary.id),
          isOssActionEditor: isOssActionEditorProfile(summary.id, ossActionEditorMemberIds),
          isReviewer: reviewerMemberIds.includes(summary.id),
          isProductionEditor: productionEditorMemberIds.includes(summary.id),
          isEditorInChief: editorInChiefMemberIds.includes(summary.id),
          ossActionEditorGroupExists: ossActionEditors.exists !== false,
          productionEditorGroupExists: productionEditors.exists !== false
        },
        actionEditorAvailabilityData: null,
        reviewerAvailabilityData: null
      };
    }
    return roleAssignmentRowsById[summary.id];
  };
  actionEditorRows.forEach(function(row) {
    var roleRow = ensureRoleAssignmentRow(row.summary);
    if (roleRow) {
      roleRow.actionEditorAvailabilityData = row.availabilityData;
    }
  });
  (ossActionEditors.members || []).forEach(function(actionEditor) {
    ensureRoleAssignmentRow(actionEditor);
  });
  (productionEditors.members || []).forEach(function(productionEditor) {
    ensureRoleAssignmentRow(productionEditor);
  });
  (editorsInChiefGroup.members || []).forEach(function(editorInChief) {
    ensureRoleAssignmentRow(editorInChief);
  });
  reviewerRows.forEach(function(row) {
    var roleRow = ensureRoleAssignmentRow(row.summary);
    if (roleRow) {
      roleRow.reviewerAvailabilityData = row.availabilityData;
    }
  });
  var toRoleAssignmentTableRow = function(row) {
    return {
      index: row.index,
      summary: row.summary,
      editorInChiefRoleData: {
        role: 'editorInChief',
        label: 'EIC',
        checked: row.roleAssignmentData.isEditorInChief,
        availabilityRole: null,
        available: true,
        disabled: false
      },
      actionEditorRoleData: {
        role: 'actionEditor',
        label: 'AE',
        checked: row.roleAssignmentData.isActionEditor || row.roleAssignmentData.isOssActionEditor,
        availabilityRole: 'actionEditor',
        availabilityData: row.actionEditorAvailabilityData,
        disabled: false
      },
      ossActionEditorRoleData: {
        role: 'ossActionEditor',
        label: 'OSS AE',
        checked: row.roleAssignmentData.isOssActionEditor,
        availabilityRole: null,
        disabled: !row.roleAssignmentData.ossActionEditorGroupExists
      },
      productionEditorRoleData: {
        role: 'productionEditor',
        label: 'PE',
        checked: row.roleAssignmentData.isProductionEditor,
        availabilityRole: null,
        available: true,
        disabled: !row.roleAssignmentData.productionEditorGroupExists
      },
      reviewerRoleData: {
        role: 'reviewer',
        label: 'Reviewer',
        checked: row.roleAssignmentData.isReviewer,
        availabilityRole: 'reviewer',
        availabilityData: row.reviewerAvailabilityData,
        disabled: false
      },
      updateRoleData: {
        roleAssignmentData: row.roleAssignmentData,
        actionEditorAvailabilityData: row.actionEditorAvailabilityData,
        reviewerAvailabilityData: row.reviewerAvailabilityData
      }
    };
  };

  return applyConsoleModel({
    pendingTaskRows: pendingTaskRows,
    activeStatusRows: activeStatusRows,
    submittedStatusRows: submittedStatusRows,
    submissionStatusRows: submissionStatusRows,
    underReviewStatusRows: underReviewStatusRows,
    underDiscussionStatusRows: underDiscussionStatusRows,
    underDecisionStatusRows: underDecisionStatusRows,
    decisionPendingStatusRows: decisionPendingStatusRows,
    cameraReadyStatusRows: cameraReadyStatusRows,
    decisionMadeStatusRows: decisionMadeStatusRows,
    reviewerStatusRows: reviewerRows.map(toReviewerStatusRow),
    actionEditorStatusRows: actionEditorRows.map(toActionEditorStatusRow),
    roleAssignmentRows: Object.values(roleAssignmentRowsById).map(toRoleAssignmentTableRow),
    roleAssignmentState: {
      editorsInChief: editorInChiefMemberIds,
      actionEditors: actionEditorMemberIds,
      ossActionEditors: ossActionEditorMemberIds,
      productionEditors: productionEditorMemberIds,
      reviewers: reviewerMemberIds,
      ossActionEditorGroupExists: ossActionEditors.exists !== false
    },
    bulkInviteTemplates: {
      reviewer: {
        content: getGroupContentValue(editorsInChiefGroup, BULK_INVITE_REVIEWER_TEMPLATE_KEY)
      },
      actionEditor: {
        content: getGroupContentValue(editorsInChiefGroup, BULK_INVITE_ACTION_EDITOR_TEMPLATE_KEY)
      }
    },
    ossActionEditorsMaxPapers: ossActionEditorsMaxPapers,
    journalStats: journalStats,
  }, 'eic', {
    rowKeys: [
      'pendingTaskRows',
      'activeStatusRows',
      'submittedStatusRows',
      'submissionStatusRows',
      'underReviewStatusRows',
      'underDiscussionStatusRows',
      'underDecisionStatusRows',
      'decisionPendingStatusRows',
      'cameraReadyStatusRows',
      'decisionMadeStatusRows'
    ]
  });
};

// Render functions
