var formatData = function(reviewersByNumber, invitations, submissions, invitationsById, customQuotaInvitation, availabilityInvitation, availabilityEdge, consoleProfileId) {
  var referrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + '#assigned-papers)');

  // build the rows
  var rows = [];
  var pendingTaskRows = [];
  submissions.forEach(function(submission) {
    var number = submission.number;
    var roleContext = resolveConsolePaperRoleContext(submission, 'ae', VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Action_Editors');
    var formattedSubmission = {
      id: submission.id,
      forum: submission.forum,
      number: number,
      cdate: submission.cdate,
      mdate: submission.mdate,
      tcdate: submission.tcdate,
      tmdate: submission.tmdate,
      showDates: true,
      content: Object.keys(submission.content).reduce(function(content, currentValue) {
        content[currentValue] = submission.content[currentValue].value;
        return content;
      }, {}),
      previousSubmissionUrl: getPreviousSubmissionUrl(submission),
      paperUrl: appendRoleContext('/forum?id=' + encodeURIComponent(submission.forum || submission.id) + '&referrer=' + referrerUrl, roleContext),
      roleContext: roleContext,
      referrer: referrerUrl,
      referrerUrl: referrerUrl
    };

    var reviews = Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, REVIEW_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });

    var decisions = Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, DECISION_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var decision = decisions.length && decisions[0];
    var reviewers = reviewersByNumber[number] || [];
    var reviewerStatus = {};

    // Build array of tasks
    var tasks = [];
    // Reviewer assignment by AE
    var reviewerAssignmentInvitation = invitationsById[getInvitationId(number, 'Assignment', REVIEWERS_NAME)];
    // Reviews by Reviewers
    var reviewInvitation = invitationsById[getInvitationId(number, REVIEW_NAME)];
    var reviewNotes = getReplies(submission, REVIEW_NAME);
    // Decision by AE
    var decisionInvitation = invitationsById[getInvitationId(number, DECISION_NAME)];
    var decisionNotes = getReplies(submission, DECISION_NAME);
    // Decision Approval by EIC
    var decisionApprovalInvitation = invitationsById[getInvitationId(number, DECISION_APPROVAL_NAME)];
    var decisionApprovalNotes = getReplies(submission, DECISION_APPROVAL_NAME);
    // Camera Ready Revision by Authors
    var cameraReadyRevisionInvitation = invitationsById[getInvitationId(number, CAMERA_READY_REVISION_NAME)];
    // Camera Ready Verification by AE
    var cameraReadyVerificationInvitation = invitationsById[getInvitationId(number, CAMERA_READY_VERIFICATION_NAME)];
    var cameraReadyVerificationNotes = getReplies(submission, CAMERA_READY_VERIFICATION_NAME);

    var venueStatusId = submission.content.venueid && submission.content.venueid.value;
    var requiredReviewers = requiredReviewerCountForSubmission(submission);
    var reviewerAssignmentLabel = 'Assign Reviewers';
    if ([ASSIGNED_AE_STATUS, UNDER_REVIEW_STATUS].includes(venueStatusId) && reviewerAssignmentInvitation && reviewers.length < requiredReviewers) {
      tasks.push({
        id: reviewerAssignmentInvitation ? reviewerAssignmentInvitation.id : getInvitationId(number, 'Assignment', REVIEWERS_NAME),
        cdate: reviewerAssignmentInvitation && reviewerAssignmentInvitation.cdate,
        duedate: reviewerAssignmentInvitation && reviewerAssignmentInvitation.duedate,
        complete: reviewers.length >= requiredReviewers,
        replies: reviewers,
        receivedCount: reviewers.length,
        requiredCount: requiredReviewers,
        assignmentLabel: reviewerAssignmentLabel,
        actions: [
          {
            name: reviewerAssignmentLabel,
            url: getReviewerAssignmentHubUrl(number)
          }
        ]
      });
    }

    if (reviewInvitation) {
      tasks.push({
        id: reviewInvitation.id,
        cdate: reviewInvitation.cdate,
        duedate: JMLRPermissionHelpers.getReviewerEffectiveDueDate(reviewInvitation),
        complete: reviewNotes.length >= requiredReviewers,
        replies: reviewNotes,
        receivedCount: reviewNotes.length,
        requiredCount: requiredReviewers,
        actionName: 'Submit decision',
        actionUrl: decisionInvitation ? appendRoleContext('/forum?id=' + submission.id +
          '&noteId=' + submission.id +
          '&invitationId=' + decisionInvitation.id +
          '&referrer=' + referrerUrl, roleContext) : null
      });
    }

    var reviewDueDate = JMLRPermissionHelpers.getReviewerEffectiveDueDate(reviewInvitation);
    var decisionPendingReady = reviewNotes.length >= requiredReviewers ||
      (reviewDueDate && reviewDueDate < Date.now());
    if (decisionInvitation && decisionPendingReady) {
      tasks.push({
        id: decisionInvitation.id,
        cdate: decisionInvitation.cdate,
        duedate: decisionInvitation.duedate,
        complete: decisionNotes.length > 0,
        replies: decisionNotes,
        actionName: 'Submit decision'
      });
    }

    if (decisionApprovalInvitation) {
      tasks.push({
        id: decisionApprovalInvitation.id,
        cdate: decisionApprovalInvitation.cdate,
        duedate: decisionApprovalInvitation.duedate,
        complete: decisionApprovalNotes.length > 0,
        replies: decisionApprovalNotes,
        actionName: 'Open decision approval'
      });
    }

    if (cameraReadyRevisionInvitation) {
      tasks.push({
        id: cameraReadyRevisionInvitation.id,
        cdate: cameraReadyRevisionInvitation.cdate,
        duedate: cameraReadyRevisionInvitation.duedate,
        complete: submission.invitations.includes(cameraReadyRevisionInvitation.id),
        replies: [],
        actionName: 'Open camera-ready revision'
      });
    }

    if (cameraReadyVerificationInvitation) {
      tasks.push({
        id: cameraReadyVerificationInvitation.id,
        cdate: cameraReadyVerificationInvitation.cdate,
        duedate: cameraReadyVerificationInvitation.duedate,
        complete: cameraReadyVerificationNotes.length > 0,
        replies: cameraReadyVerificationNotes,
        actionName: 'Verify camera-ready revision'
      });
    }


    reviewers.forEach(function(reviewer) {
      var completedReview = reviews.find(function(review) { return review.signatures[0].endsWith('/Reviewer_' + reviewer.anonId); });
      var reviewerRating = submission.details.replies.find(function (p) {
        return p.invitations.includes(VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Reviewer_' + reviewer.anonId + '/-/Rating') &&
          (
            p.replyto === (completedReview && completedReview.id) ||
            p.replyto === submission.id ||
            p.content && p.content.reviewer_anon_id && String(p.content.reviewer_anon_id.value) === String(reviewer.anonId)
          );
      });
      var status = {
        'profileID': reviewer.id
      };
      var links = {};

      if (completedReview) {
        if (completedReview.content && completedReview.content.recommendation_for_acceptance) {
          status.Recommendation = completedReview.content.recommendation_for_acceptance.value;
        }
      }
      if(reviewerRating){
        status.Rating = reviewerRating.content.rating.value;
      }
      reviewerStatus[reviewer.anonId] = {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
        completedReview: completedReview && true,
        forum: submission.id,
        note: completedReview && completedReview.id,
        status: status,
        links: links,
        forumUrl: '/forum?' + $.param({
          id: submission.id,
          noteId: submission.id,
          invitationId: Webfield2.utils.getInvitationId(VENUE_ID, submission.number, REVIEW_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME })
        }),
        paperNumber: number,
        anonymousGroupId: reviewer.anonymousGroupId
      };
    });

    var reviewerAssignmentActions = ([ASSIGNED_AE_STATUS, UNDER_REVIEW_STATUS].includes(venueStatusId) && reviewerAssignmentInvitation) ? [
      {
        name: reviewerAssignmentLabel,
        url: getReviewerAssignmentHubUrl(number)
      }
    ] : [];

    rows.push({
      submissionNumber: { number: parseInt(number) },
      submission: ({
        ...formattedSubmission,
        beyondPdf: submission.content.beyond_pdf?.value !== undefined
      }),
      reviewProgressData: {
        noteId: submission.id,
        paperNumber: number,
        numSubmittedReviews: reviews.length,
        numReviewers: reviewers.length,
        requiredReviewers: requiredReviewers,
        reviewers: reviewerStatus,
        expandReviewerList: true,
        sendReminder: true,
        showPreferredEmail: PREFERRED_EMAILS_ID,
        referrer: referrerUrl,
        actions: reviewerAssignmentActions,
        duedate: JMLRPermissionHelpers.getReviewerEffectiveDueDate(reviewInvitation)
      },
      actionEditorData: {
        committeeName: 'Action Editor',
        recommendation: decision && decision.content.recommendation.value,
        editUrl: decision ? appendRoleContext('/forum?id=' + submission.id + '&noteId=' + decision.id + '&referrer=' + referrerUrl, roleContext) : null
      }
    });

    pendingTaskRows.push({
      tasks: tasks,
      forumId: submission.id,
      submissionNumber: number,
      submissionTitle: formattedSubmission.content.title,
      roleContext: roleContext
    });

  });

  var pendingReferrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + '#pending-tasks)');
  var pendingTaskInvitations = [];
  pendingTaskRows.forEach(function(row) {
    row.tasks.filter(function(task) {
      return isPendingTaskVisible(task);
    }).forEach(function(task) {
      var paperUrl = appendRoleContext('/forum?id=' + row.forumId + '&referrer=' + pendingReferrerUrl, row.roleContext);
      var taskUrl = paperUrl;
      if (task.id.split('/-/').pop() === DECISION_NAME) {
        taskUrl = appendRoleContext('/forum?id=' + row.forumId +
          '&noteId=' + row.forumId +
          '&invitationId=' + task.id +
          '&referrer=' + pendingReferrerUrl, row.roleContext);
      } else if (task.id.split('/-/').pop() === CAMERA_READY_VERIFICATION_NAME) {
        taskUrl = appendRoleContext('/forum?id=' + row.forumId +
          '&noteId=' + row.forumId +
          '&invitationId=' + task.id +
          '&referrer=' + pendingReferrerUrl, row.roleContext);
      }
      var taskActions = task.actions || [];
      var taskActionUrl = task.actionUrl || taskUrl;
      if (!taskActions.length && taskActionUrl) {
        taskActions = [{
          name: getTaskActionLabel(task),
          url: taskActionUrl
        }];
      }
      pendingTaskInvitations.push({
        id: task.id,
        cdate: task.cdate,
        duedate: task.duedate,
        forumId: row.forumId,
        submissionNumber: row.submissionNumber,
        submissionTitle: row.submissionTitle,
        receivedCount: task.receivedCount,
        requiredCount: task.requiredCount,
        assignmentLabel: task.assignmentLabel,
        actions: taskActions,
        roleContext: row.roleContext,
        url: paperUrl
      });
    });
  });

  return applyConsoleModel({
    invitations: pendingTaskInvitations,
    rows: rows,
    activeRows: rows.filter(isActiveActionEditorRow),
    customQuotaInvitation: customQuotaInvitation,
    availabilityInvitation: availabilityInvitation,
    availabilityEdge: availabilityEdge,
    consoleProfileId: consoleProfileId
  }, 'ae', { rowKeys: ['rows', 'activeRows'], pendingTaskKeys: ['invitations'] });
};

// Render functions
