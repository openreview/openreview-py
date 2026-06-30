var getInvitationId = function(number, name, prefix) {
  return Webfield2.utils.getInvitationId(VENUE_ID, number, name, { prefix: prefix, submissionGroupName: SUBMISSION_GROUP_NAME })
};

var getPreviousSubmissionUrl = function(submission) {
  var field = submission.content.previous_JMLR_submission_URL;
  var value = field && field.value;
  return value && value !== 'N/A' ? value : null;
};

var renderPreviousSubmissionLink = function(data) {
  var content = data.content || {};
  var previousHtml = JMLRPermissionHelpers.renderPreviousSubmissionsList(
    getContentValue(content, 'previous_JMLR_submissions'),
    getContentValue(content, 'previous_JMLR_submission_number'),
    data.previousSubmissionUrl || getContentValue(content, 'previous_JMLR_submission_URL')
  );
  return previousHtml ? '<div class="mt-2 mb-0"><strong>Previous JMLR Submissions:</strong>' + previousHtml + '</div>' : '';
};

var getContentValue = function(content, fieldName) {
  var field = content && content[fieldName];
  return field && field.value !== undefined ? field.value : field;
};

var requiredReviewerCountForSubmission = function(submission) {
  var value = Number(getContentValue((submission && submission.content) || {}, 'reviews_required_count'));
  return value && value > 0 ? value : NUMBER_OF_REVIEWERS;
};

var isNonEmptyAttachment = function(value) {
  return value !== undefined && value !== null && String(value).trim() && String(value).trim().toUpperCase() !== 'N/A';
};

var renderAuthorChangeMetadata = function(content) {
  var previousAuthorNames = String(getContentValue(content, 'previous_author_names') || '').trim();
  var currentAuthorNames = String(getContentValue(content, 'current_author_names') || '').trim();
  var authorChangeSummary = String(getContentValue(content, 'author_change_summary') || '').trim();
  if (!previousAuthorNames && !currentAuthorNames && !authorChangeSummary) {
    return '';
  }
  return '<details style="margin-top: 6px;"><summary><strong>Resubmission Author-List Difference</strong></summary>' +
    '<div class="alert alert-warning" style="margin: 8px 0;">Only author ordering changes are allowed for resubmissions. Adding, removing, replacing, renaming, or otherwise changing authors is not allowed. Impermissible author changes may cause desk rejection or later rejection at editorial discretion. This warning is informational and does not block submission.</div>' +
    '<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px;">' +
      '<div><strong>Previous authors</strong><pre style="white-space: pre-wrap; margin: 6px 0 0; background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; padding: 8px;">' + _.escape(previousAuthorNames || 'Not available') + '</pre></div>' +
      '<div><strong>Current authors</strong><pre style="white-space: pre-wrap; margin: 6px 0 0; background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; padding: 8px;">' + _.escape(currentAuthorNames || 'Not available') + '</pre></div>' +
    '</div>' +
    '<p style="margin: 8px 0 0;"><strong>Diff:</strong> ' + _.escape(authorChangeSummary || 'Not available') + '</p>' +
    '</details>';
};

var renderJmlrSubmissionDetails = function(submission) {
  var content = submission.content || {};
  var paperId = submission.id || submission.forum;
  var pdfUrl = '/pdf?id=' + encodeURIComponent(paperId);
  var supplementaryValue = getContentValue(content, 'supplementary_material');
  var replyToReviewersValue = getContentValue(content, 'response_to_reviewers');
  var coverLetter = String(getContentValue(content, 'cover_letter') || '').trim();
  var authorList = String(getContentValue(content, 'author_list') || '').trim();
  var ossValue = getContentValue(content, 'open_source_software');
  var isOss = ossValue === true || ossValue === 'true' || ossValue === 'Yes';
  var previousNumber = String(getContentValue(content, 'previous_JMLR_submission_number') || '').trim();
  var previousUrl = String(getContentValue(content, 'previous_JMLR_submission_URL') || submission.previousSubmissionUrl || '').trim();
  var previousSubmissionsHtml = JMLRPermissionHelpers.renderPreviousSubmissionsList(
    getContentValue(content, 'previous_JMLR_submissions'),
    previousNumber,
    previousUrl
  );
  return '<div class="jmlr-submission-metadata" style="margin-top: 8px; font-size: 13px; line-height: 1.4;">' +
    '<details><summary><strong>Submission Metadata</strong></summary><div style="margin-top: 8px;">' +
    '<p style="margin-bottom: 6px;"><strong>Main Paper PDF:</strong> <a href="' + pdfUrl + '" target="_blank" rel="noopener noreferrer">Open PDF</a></p>' +
    (isNonEmptyAttachment(supplementaryValue) ? '<p style="margin-bottom: 6px;"><strong>Supplementary Material:</strong> <a href="/attachment?id=' + encodeURIComponent(paperId) + '&name=supplementary_material" target="_blank" rel="noopener noreferrer">Open supplementary material</a></p>' : '') +
    (isNonEmptyAttachment(replyToReviewersValue) ? '<p style="margin-bottom: 6px;"><strong>Response to Reviewers:</strong> <a href="/attachment?id=' + encodeURIComponent(paperId) + '&name=response_to_reviewers" target="_blank" rel="noopener noreferrer">Open response to reviewers</a></p>' : '') +
    '<p style="margin-bottom: 6px;"><strong>Open Source Software:</strong> ' + (isOss ? 'Yes' : 'No') + '</p>' +
    (previousSubmissionsHtml ? '<div style="margin-bottom: 6px;"><strong>Previous JMLR Submissions:</strong>' + previousSubmissionsHtml + '</div>' : '') +
    renderAuthorChangeMetadata(content) +
    '<details style="margin-top: 6px;"><summary><strong>Cover Letter</strong></summary><pre style="white-space: pre-wrap; margin: 6px 0 0; background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; padding: 8px;">' + _.escape(coverLetter || 'No cover letter was provided.') + '</pre></details>' +
    '<details style="margin-top: 6px;"><summary><strong>Author List</strong></summary><pre style="white-space: pre-wrap; margin: 6px 0 0; background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; padding: 8px;">' + _.escape(authorList || 'No author list was provided.') + '</pre></details>' +
    '</div></details></div>';
};

var getReplies = function(submission, name, prefix) {
  return Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, name, { prefix: prefix, submissionGroupName: SUBMISSION_GROUP_NAME });
};

var getReviewerAssignmentHubUrl = function(paperNumber) {
  return '/group?id=' + encodeURIComponent(VENUE_ID + '/' + SUBMISSION_GROUP_NAME + paperNumber + '/' + REVIEWERS_NAME) +
    '&referrer=' + encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + '#assigned-papers)');
};

var getTaskLabel = function(task) {
  return 'Paper ' + task.submissionNumber + (task.submissionTitle ? ': ' + task.submissionTitle : '');
};

var getTaskActionLabel = function(task) {
  if (task.assignmentLabel) return task.assignmentLabel;
  if (task.actionName) return task.actionName;
  var taskNameByInvitation = {};
  taskNameByInvitation[REVIEW_NAME] = 'Submit decision';
  taskNameByInvitation[DECISION_NAME] = 'Submit decision';
  taskNameByInvitation[CAMERA_READY_VERIFICATION_NAME] = 'Verify camera-ready revision';
  var rawTaskName = task.id.split('/-/').pop().replace(/_/g, ' ');
  return taskNameByInvitation[rawTaskName] || rawTaskName;
};

var getTaskDueDate = function(task) {
  if (!task.duedate) return '';
  return ' Due: ' + new Date(task.duedate).toLocaleString('en-US', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'long'
  });
};

var formatDate = function(timestamp) {
  return new Date(timestamp).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC'
  });
};

var isPendingTaskVisible = function(task) {
  if (task.complete) return false;
  var rawTaskName = task.id.split('/-/').pop().replace(/_/g, ' ');
  if (rawTaskName === REVIEW_NAME) {
    return task.duedate && task.duedate < Date.now();
  }
  return true;
};

var isAcceptedDecisionRecommendation = function(recommendation) {
  return String(recommendation || '').indexOf('Accept') === 0;
};

var isPublicationApprovedStatus = function(venueStatusId) {
  return [
    CAMERA_READY_APPROVED_STATUS,
    CAMERA_READY_PUBLISHED_STATUS,
    PUBLICATION_RETRACTED_STATUS
  ].indexOf(venueStatusId) >= 0;
};

var isActiveActionEditorRow = function(row) {
  var recommendation = row && row.actionEditorData && row.actionEditorData.recommendation;
  if (!recommendation) return true;
  return isAcceptedDecisionRecommendation(recommendation) &&
    !isPublicationApprovedStatus(getContentValue(row.submission && row.submission.content || {}, 'venueid'));
};

var getEdgeWeight = function(edge, fallback) {
  var weight = edge && edge.weight;
  return weight === undefined || weight === null ? fallback : Number(weight);
};

var isAssignmentAvailable = function(edge) {
  if (!edge || edge.label !== 'Unavailable') return true;
  return edge.weight && Number(edge.weight) <= Date.now();
};

var getReviewerAutoAssignmentSignature = function(paperNumber) {
  var profileId = user && user.profile && user.profile.id || user && user.id;
  if (!profileId) return $.Deferred().reject('Could not determine your OpenReview profile signature.').promise();

  return Webfield2.api.get('/groups', {
    prefix: VENUE_ID + '/' + SUBMISSION_GROUP_NAME + paperNumber + '/Action_Editor_',
    signatory: profileId
  }).then(function(result) {
    var groups = result.groups || [];
    if (!groups.length) {
      return $.Deferred().reject('Could not find your anonymous action editor group for paper ' + paperNumber + '.').promise();
    }
    return groups[0].id;
  });
};

var getEdgesByTail = function(invitationId, head, tails) {
  var requests = tails.map(function(tail) {
    var params = { invitation: invitationId, tail: tail, domain: VENUE_ID };
    if (head) params.head = head;
    return Webfield2.api.getAll('/edges', params).then(function(edges) {
      return { tail: tail, edges: edges || [] };
    });
  });

  return $.when.apply($, requests).then(function() {
    var results = requests.length === 1 ? [arguments[0]] : Array.prototype.slice.call(arguments);
    return results.reduce(function(byTail, result) {
      byTail[result.tail] = result.edges;
      return byTail;
    }, {});
  });
};
