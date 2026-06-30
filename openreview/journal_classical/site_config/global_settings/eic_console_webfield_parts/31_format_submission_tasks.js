    // Reviewer assignment by AE
    var aeAssignmentInvitation = invitationsById[getInvitationId(number, 'Assignment', ACTION_EDITOR_NAME)];
    var reviewerAssignmentInvitation = invitationsById[getInvitationId(number, 'Assignment', REVIEWERS_NAME)];
    var assignActionEditorWrapperInvitation = invitationsById[getInvitationId(number, 'Assign_Action_Editor')];
    var setupReadinessNote = (setupAssignmentNotes || []).find(function(setupNote) {
      return setupReadinessMatchesPaper(setupNote, submission);
    });
    var assignmentSetupState = classifyAssignmentSetupNotesForPaper(setupAssignmentNotes || [], submission, Date.now());
    var setupReadinessStatus = getContentValue(setupReadinessNote && setupReadinessNote.content, 'setup_readiness_status') || '';
    var hasAssignmentSurfaces = Boolean(aeAssignmentInvitation && reviewerAssignmentInvitation && assignActionEditorWrapperInvitation);
    if (setupReadinessStatus === SETUP_STATUS_READY && hasAssignmentSurfaces) {
      assignmentSetupState.status = 'complete';
    }
    var assignmentSetupData = {
      hasSetupReadiness: setupReadinessStatus === 'Assignment pages created',
      hasAssignmentSurfaces: hasAssignmentSurfaces,
      setupStateStatus: assignmentSetupState.status,
      setupInProgressNoteId: assignmentSetupState.inProgressNoteId,
      setupInProgressStartedAt: assignmentSetupState.inProgressStartedAt,
      setupInProgressAgeMs: assignmentSetupState.ageMs,
      failedSetupNoteId: assignmentSetupState.failedNoteId,
      setupReadinessStatus: setupReadinessStatus,
      setupReadinessNoteId: setupReadinessNote && setupReadinessNote.id || '',
      actionEditorAssignmentInvitationId: aeAssignmentInvitation && aeAssignmentInvitation.id || '',
      reviewerAssignmentInvitationId: reviewerAssignmentInvitation && reviewerAssignmentInvitation.id || '',
      assignActionEditorInvitationId: assignActionEditorWrapperInvitation && assignActionEditorWrapperInvitation.id || ''
    };
    // Reviews by Reviewers
    var reviewInvitation = invitationsById[getInvitationId(number, REVIEW_NAME)];
    var reviewNotes = getReplies(submission, REVIEW_NAME);
    var requiredReviewers = requiredReviewerCountForSubmission(submission);
    // Reviewer Rating by AE
    var reviewerRatingInvitations = getRatingInvitations(invitationsById, number, reviewers);
    var reviewerRatingReplies = getRatingReplies(submission, reviewerRatingInvitations);
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
    var cameraReadyTask = null;
    var cameraReadyVerificationTask = null;
    // Retraction by Authors
    var retractionInvitation = invitationsById[getInvitationId(number, RETRACTION_NAME)];
    var retractionNotes = getReplies(submission, RETRACTION_NAME);
    // Retraction Approval by EIC
    var retractionApprovalInvitation = invitationsById[getInvitationId(number, RETRACTION_APPROVAL_NAME)];
    var retractionApprovalNotes = getReplies(submission, RETRACTION_APPROVAL_NAME);

    var earlylateTaskDueDate = 0;

    if (aeRecommendationInvitation) {
      var recommendationCount = aeRecommendations[submission.id] || 0;
      var task = {
        id: aeRecommendationInvitation.id,
        cdate: aeRecommendationInvitation.cdate,
        duedate: aeRecommendationInvitation.duedate,
        complete: recommendationCount >= requiredReviewers,
        replies: Array(recommendationCount).fill(1)
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);
    }

    if (reviewerAssignmentInvitation) {
      var reviewers = reviewersByNumber[number] || [];
      var task = {
        id: reviewerAssignmentInvitation.id,
        cdate: reviewerAssignmentInvitation.cdate,
        duedate: reviewerAssignmentInvitation.duedate,
        complete: reviewers.length >= requiredReviewers,
        replies: reviewers
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);     
    }

    if (reviewInvitation) {
      var task = {
        id: reviewInvitation.id,
        cdate: reviewInvitation.cdate,
        duedate: JMLRPermissionHelpers.getReviewerEffectiveDueDate(reviewInvitation),
        complete: reviewNotes.length >= requiredReviewers,
        replies: reviewNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);         
    }

    if (reviewerRatingInvitations.length) {
      var task = {
        id: getInvitationId(number, 'Reviewer_Rating'),
        cdate: reviewerRatingInvitations[0].cdate,
        duedate: reviewerRatingInvitations[0].duedate,
        complete: reviewerRatingReplies.length == reviewers.length,
        replies: reviewerRatingReplies,
        receivedCount: reviewerRatingReplies.length,
        requiredCount: reviewers.length
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);      
    }

    if (decisionInvitation) {
      var task = {
        id: decisionInvitation.id,
        cdate: decisionInvitation.cdate,
        duedate: decisionInvitation.duedate,
        complete: decisionNotes.length > 0,
        replies: decisionNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);      
    }

    if (decisionApprovalInvitation) {
      var task = {
        id: decisionApprovalInvitation.id,
        cdate: decisionApprovalInvitation.cdate,
        duedate: decisionApprovalInvitation.duedate,
        complete: decisionApprovalNotes.length > 0,
        replies: decisionApprovalNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);      
      if (!task.complete) {
        incompleteEicTasks.push([
          {
            id: formattedSubmission.id,
            title: formattedSubmission.content.title || formattedSubmission.number
          },
          task
        ]);
      }
    }

    if (cameraReadyRevisionInvitation) {
      var complete = submission.invitations.includes(cameraReadyRevisionInvitation.id);
      cameraReadyTask = {
        id: cameraReadyRevisionInvitation.id,
        cdate: cameraReadyRevisionInvitation.cdate,
        duedate: cameraReadyRevisionInvitation.duedate,
        complete: complete,
        replies: complete ? [1] : []
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, cameraReadyTask);
      tasks.push(cameraReadyTask);      
    }

    if (cameraReadyVerificationInvitation) {
      cameraReadyVerificationTask = {
        id: cameraReadyVerificationInvitation.id,
        cdate: cameraReadyVerificationInvitation.cdate,
        duedate: cameraReadyVerificationInvitation.duedate,
        complete: cameraReadyVerificationNotes.length > 0,
        replies: cameraReadyVerificationNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, cameraReadyVerificationTask);
      tasks.push(cameraReadyVerificationTask);      
    }

    if (retractionApprovalInvitation) {
      var task = {
        id: retractionApprovalInvitation.id,
        cdate: retractionApprovalInvitation.cdate,
        duedate: retractionApprovalInvitation.duedate,
        complete: retractionApprovalNotes.length > 0,
        replies: retractionApprovalNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);      
      if (!task.complete) {
        incompleteEicTasks.push([
          {
            id: formattedSubmission.id,
            title: formattedSubmission.content.title || formattedSubmission.number
          },
          task
        ]);
      }
    }    

    var reviews = reviewNotes;
    var decisions = decisionNotes;
    var paperReviewers = reviewersByNumber[number] || [];
    var paperReviewerStatus = {};
    var completedReviews = reviews.length && (reviews.length == paperReviewers.length);

    paperReviewers.forEach(function(reviewer) {
      var completedReview = reviews.find(function(review) { return review.signatures[0].endsWith('/Reviewer_' + reviewer.anonId); });
      var reviewerRating = reviewerRatingReplies.find(function (p) {
        return p.invitations.includes(VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Reviewer_' + reviewer.anonId + '/-/Rating') &&
          (
            p.replyto === (completedReview && completedReview.id) ||
            p.replyto === submission.id ||
            p.content && p.content.reviewer_anon_id && String(p.content.reviewer_anon_id.value) === String(reviewer.anonId)
          );
      });
      var status = {};
      var reviewerStatus = reviewerStatusById[reviewer.id];
      var links = {};
      if (completedReview) {
        if (completedReview.content && completedReview.content.recommendation_for_acceptance) {
          status.Recommendation = completedReview.content.recommendation_for_acceptance.value;
        }
      }
      if(reviewerRating){
        status.Rating = reviewerRating.content.rating.value;
        if(reviewerStatus){
          reviewerStatus.ratingData = JMLRPermissionHelpers.addReviewerRating(reviewerStatus.ratingData, reviewerRating, REVIEWER_RATING_MAP);
        }
      }
      paperReviewerStatus[reviewer.anonId] = {
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
          invitationId: getInvitationId(submission.number, REVIEW_NAME)
        }),
        anonymousGroupId: reviewer.anonymousGroupId
      }

      if (reviewerStatus) {
        reviewerStatus.reviewerProgressData.numPapers += 1;
        reviewerStatus.reviewerStatusData.numPapers += 1;
        reviewerStatus.reviewerProgressData.papers.push({ note: formattedSubmission, review: completedReview ? { forum: completedReview.forum, status: status } : null});
        reviewerStatus.reviewerStatusData.papers.push({
            note: formattedSubmission,
            numOfReviews: reviews.length,
            numOfReviewers: paperReviewers.length
        });
        if (completedReview){
          reviewerStatus.reviewerProgressData.numCompletedReviews += 1;
        }
        if (completedReviews) {
          reviewerStatus.reviewerStatusData.numCompletedReviews += 1;
        }
      }
    });

    paperActionEditors.forEach(function(actionEditor) {
      var completedDecision = decisions.find(function(decision) { return decision.signatures[0].startsWith(VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Action_Editor'); });
      var actionEditorStatus = actionEditorStatusById[actionEditor.id];
      if (actionEditorStatus) {
        actionEditorStatus.reviewProgressData.numPapers += 1;
        actionEditorStatus.decisionProgressData.numPapers += 1;
        var assignmentEdge = (actionEditorAssignmentEdgesByHead[submission.id] || []).find(function(edge) {
          return edge.tail === actionEditor.id;
        });
        var decisionTiming = JMLRPermissionHelpers.getActionEditorDecisionTiming(assignmentEdge, completedDecision, Date.now());
        if (completedDecision){
          actionEditorStatus.decisionProgressData.numCompletedMetaReviews += 1;
          if (decisionTiming.has_timing) {
            if (decisionTiming.elapsed <= DECISION_WITHIN_SIX_MONTHS_MS) {
              actionEditorStatus.decisionTimingData.completedWithinSixMonths += 1;
            }
            if (decisionTiming.elapsed <= DECISION_WITHIN_NINE_MONTHS_MS) {
              actionEditorStatus.decisionTimingData.completedWithinNineMonths += 1;
            }
            if (decisionTiming.elapsed > DECISION_OVER_TWELVE_MONTHS_MS) {
              actionEditorStatus.decisionTimingData.completedOverTwelveMonths += 1;
            }
          }
        } else if (decisionTiming.has_timing && decisionTiming.elapsed <= DECISION_WITHIN_SIX_MONTHS_MS) {
          actionEditorStatus.decisionTimingData.pendingWithinSixMonths += 1;
        }
        if (completedReviews) {
          actionEditorStatus.reviewProgressData.numCompletedReviews += 1;
        }
        actionEditorStatus.reviewProgressData.papers.push({
            note: formattedSubmission,
            numOfReviews: reviews.length,
            numOfReviewers: paperReviewers.length
        });
        actionEditorStatus.decisionProgressData.papers.push({
          note: formattedSubmission,
          metaReview: completedDecision && { id: completedDecision.id, forum: submission.id, content: { recommendation: completedDecision.content.recommendation.value }}
        });
      }
    });

    var metaReview = null;
    var decision = decisions.length > 0 ? decisions[0] : null;
    if (decision) {
      metaReview = {
        id: decision.id,
        forum: submission.id,
        content: {
          recommendation: decision.content.recommendation.value,
          certification: (decision.content.certifications && decision.content.certifications.value) || []
        }
      };
    }

    overdueTasks.concat(tasks.filter(function(inv) { return !inv.complete; }));

    var aeAssignmentUrl = getActionEditorAssignmentPageUrl(submission);
    var isResubmissionWithoutActionEditor = hasPreviousSubmissionReference(submission) && !paperActionEditors.length;
    var previousContinuity = {
      hasPreviousSubmissionReference: hasPreviousSubmissionReference(submission),
      hasAssignmentSurfaces: assignmentSetupData.hasSetupReadiness && assignmentSetupData.hasAssignmentSurfaces,
      noteId: submission.id,
      paperNumber: number,
      previousUrl: getContentValue(submission.content, 'previous_JMLR_submission_URL') || formattedSubmission.previousSubmissionUrl || '',
      previousNumber: getContentValue(submission.content, 'previous_JMLR_submission_number') || '',
      previousList: getContentValue(submission.content, 'previous_JMLR_submissions') || ''
    };
    formattedSubmission.previousContinuity = previousContinuity;
    var aeActions = (assignmentSetupData.hasSetupReadiness && assignmentSetupData.hasAssignmentSurfaces && !isResubmissionWithoutActionEditor && canShowEicAeAssignmentAction(submission, decisions, paperActionEditors)) ? [
      {
        name: paperActionEditors.length ? 'Edit action editor assignment' : 'Assign Action Editor',
        url: aeAssignmentUrl
      }
    ] : [
