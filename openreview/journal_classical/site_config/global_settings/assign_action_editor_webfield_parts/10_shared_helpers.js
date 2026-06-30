
// Helpers
var getInvitationId = function(number, name, prefix) {
  return Webfield2.utils.getInvitationId(VENUE_ID, number, name, { prefix: prefix, submissionGroupName: SUBMISSION_GROUP_NAME })
};

var actionEditorAssignmentBrowserContract = function() {
  return typeof ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT !== 'undefined' && ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT
    ? ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT
    : {};
};

var actionEditorAssignmentContractSection = function(sectionName) {
  var section = actionEditorAssignmentBrowserContract()[sectionName];
  return section && typeof section === 'object' ? section : {};
};

var actionEditorAssignmentInvitationId = function() {
  return actionEditorAssignmentBrowserContract().assignment_invitation || PAPER_ACTION_EDITORS_ASSIGNMENT_ID;
};

var actionEditorAssignmentReadbackSources = function() {
  var sources = actionEditorAssignmentBrowserContract().readback_assignment_sources;
  if (Array.isArray(sources) && sources.length) return sources;
  return [actionEditorAssignmentInvitationId()].filter(Boolean);
};

var actionEditorReviewerEntrySources = function(submission) {
  var sources = actionEditorAssignmentContractSection('reviewer_entry_sources');
  return {
    reviewerAssignmentInvitation: sources.reviewer_assignment_invitation || VENUE_ID + '/Paper' + submission.number + '/Reviewers/-/Assignment',
    paperReviewersGroup: sources.paper_reviewers_group || VENUE_ID + '/Paper' + submission.number + '/Reviewers'
  };
};

var actionEditorAssignmentScoreSources = function() {
  var sources = actionEditorAssignmentContractSection('score_sources');
  return {
    affinityScoreInvitation: sources.affinity_score_invitation || ACTION_EDITORS_AFFINITY_SCORE_ID,
    matchingInputGroup: sources.matching_input_group || ACTION_EDITOR_ID
  };
};

var actionEditorAssignmentConflictSources = function() {
  var sources = actionEditorAssignmentContractSection('conflict_sources');
  return {
    openreviewConflictInvitation: sources.openreview_conflict_invitation || ACTION_EDITORS_CONFLICT_ID,
    reviewerConflictInvitation: sources.reviewer_conflict_invitation || REVIEWERS_CONFLICT_ID,
    candidateRefreshInvitation: sources.candidate_refresh_invitation || VENUE_ID + '/-/Action_Editor_Candidate_Conflict_Refresh'
  };
};

var actionEditorAssignmentAvailabilitySources = function() {
  var sources = actionEditorAssignmentContractSection('availability_sources');
  return {
    actionEditorAvailabilityInvitation: sources.action_editor_availability_invitation || ACTION_EDITORS_AVAILABILITY_ID,
    actionEditorGroup: sources.action_editor_group || ACTION_EDITOR_ID
  };
};

var actionEditorAssignmentLoadSources = function() {
  var sources = actionEditorAssignmentContractSection('load_sources');
  return {
    customMaxPapersInvitation: sources.custom_max_papers_invitation || ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID,
    assignmentHistorySources: Array.isArray(sources.assignment_history_sources) && sources.assignment_history_sources.length
      ? sources.assignment_history_sources
      : [actionEditorAssignmentInvitationId(), ACTION_EDITORS_ASSIGNMENT_ID, ACTION_EDITORS_ARCHIVED_ASSIGNMENT_ID]
  };
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

var canShowEicAeAssignmentAction = function(submission, decisions, paperActionEditors) {
  var helpers = typeof JMLRPermissionHelpers !== 'undefined' ? JMLRPermissionHelpers : null;
  if (helpers && helpers.getEicPaperActionPolicy && helpers.loadPaperContext) {
    var paperContext = helpers.loadPaperContext({ submission: submission }).model.paper_context;
    return helpers.getEicPaperActionPolicy(null, paperContext, {
      decisions: decisions || [],
      paper_action_editors: paperActionEditors || [],
      venue_context: {
        venue_id: VENUE_ID,
        role_groups: {
          author: AUTHORS_ID,
          reviewer: REVIEWERS_ID,
          ae: ACTION_EDITOR_ID,
          eic: EDITORS_IN_CHIEF_ID,
          pe: PRODUCTION_EDITORS_ID
        }
      }
    }).model.show_ae_assignment_action;
  }
  var venueId = getContentValue(submission.content, 'venueid');
  var hasDecision = (decisions || []).length > 0;
  if (hasDecision) return false;
  var preDecisionStatuses = [
    SUBMITTED_STATUS,
    ASSIGNING_AE_STATUS,
    ASSIGNED_AE_STATUS,
    UNDER_REVIEW_STATUS,
    DECISION_PENDING_STATUS
  ];
  if (preDecisionStatuses.indexOf(venueId) < 0) return false;
  return venueId !== UNDER_REVIEW_STATUS || (paperActionEditors || []).length > 0;
};

var getContentValue = function(content, fieldName) {
  var field = content && content[fieldName];
  return field && field.value !== undefined ? field.value : field;
};

var requiredReviewerCountForSubmission = function(submission) {
  var value = Number(getContentValue((submission && submission.content) || {}, 'reviews_required_count'));
  return value && value > 0 ? value : NUMBER_OF_REVIEWERS;
};

var safeReloadPage = function() {
  var pageLocation =
    (typeof globalThis !== 'undefined' && globalThis.location) ||
    (typeof document !== 'undefined' && document && document.location) ||
    (typeof location !== 'undefined' && location);
  if (pageLocation && pageLocation.href) {
    try {
      var url = new URL(pageLocation.href);
      url.searchParams.set('_jmlr_refresh', String(Date.now()));
      pageLocation.href = url.toString();
      return;
    } catch (error) {
      pageLocation.href = pageLocation.href;
      return;
    }
  }
  if (pageLocation && typeof pageLocation.reload === 'function') {
    pageLocation.reload();
  }
};

var isOssActionEditorProfile = function(profileId, ossActionEditorIds) {
  if (!profileId) return false;
  if (!ossActionEditorIds) return false;
  if (ossActionEditorIds instanceof Set) return ossActionEditorIds.has(profileId);
  return (ossActionEditorIds || []).indexOf(profileId) >= 0;
};

var currentUserIdentityValues = function() {
  if (!user || user.isGuest) return [];
  var ids = [];
  var add = function(value) {
    if (!value) return;
    if (Array.isArray(value)) {
      value.forEach(add);
      return;
    }
    ids.push(value);
  };
  add(user.id);
  if (user.profile) {
    add(user.profile.id);
    add(user.profile.preferredId);
    add(user.profile.preferredEmail);
    add(user.profile.emails);
    add(user.profile.confirmedEmails);
    add(user.profile.usernames);
  }
  return _.uniq(ids.filter(Boolean));
};

var currentUserIsEic = function(editorsInChiefGroup) {
  var ids = currentUserIdentityValues();
  return (editorsInChiefGroup.members || []).some(function(member) {
    return ids.indexOf(member) >= 0;
  });
};

var appendRoleContext = function(url, roleContext) {
  if (!url || !roleContext) return url;
  var separator = url.indexOf('?') >= 0 ? '&' : '?';
  return url + separator + 'role_context=' + encodeURIComponent(roleContext);
};

var getUrlArgument = function(name) {
  if (typeof args !== 'undefined' && args && args[name]) return String(args[name]);
  var pageLocation =
    (typeof globalThis !== 'undefined' && globalThis.location) ||
    (typeof document !== 'undefined' && document && document.location) ||
    (typeof location !== 'undefined' && location);
  var search = pageLocation && pageLocation.search || '';
  if (!search && pageLocation && pageLocation.href && pageLocation.href.indexOf('?') >= 0) {
    search = '?' + pageLocation.href.split('?', 2)[1].split('#', 1)[0];
  }
  if (!search) return null;
  if (typeof URLSearchParams !== 'undefined') {
    var params = new URLSearchParams(search.charAt(0) === '?' ? search.slice(1) : search);
    return params.get(name);
  }
  var pattern = new RegExp('[?&]' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '=([^&#]*)');
  var match = pattern.exec(search);
  return match ? decodeURIComponent(match[1].replace(/\+/g, ' ')) : null;
};

var getAssignActionEditorRoleContext = function() {
  return getUrlArgument('role_context') || 'eic';
};

var assignmentPageHasEicRoleContext = function() {
  return getAssignActionEditorRoleContext() === 'eic';
};

var resolveConsolePaperRoleContext = function(submission, roleContext, membershipId) {
  var helpers = typeof JMLRPermissionHelpers !== 'undefined' ? JMLRPermissionHelpers : null;
  if (!helpers || !helpers.loadActorContext || !helpers.loadPaperContext || !helpers.resolveRoleContext) {
    return roleContext;
  }
  var actorContext = helpers.loadActorContext(user || {}, {
    memberships: [membershipId].filter(Boolean)
  }).model.actor_context;
  var paperContext = helpers.loadPaperContext({
    submission: submission,
    groups: {}
  }).model.paper_context;
  var resolved = helpers.resolveRoleContext(actorContext, paperContext, {
    entry_point: roleContext + '_console',
    requested_role_context: roleContext,
    venue_context: {
      venue_id: VENUE_ID,
      role_groups: {
        eic: EDITORS_IN_CHIEF_ID,
        pe: PRODUCTION_EDITORS_ID
      }
    }
  });
  return resolved.model.role_context || roleContext;
};

var applyConsoleModel = function(venueStatusData, roleContext, options) {
  options = options || {};
  var helpers = typeof JMLRPermissionHelpers !== 'undefined' ? JMLRPermissionHelpers : null;
  if (!helpers || !helpers.loadActorContext || !helpers.loadVenueContext || !helpers.getConsoleModel) {
    return venueStatusData;
  }
  var actorContext = helpers.loadActorContext(user || {}).model.actor_context;
  var venueContext = helpers.loadVenueContext({
    venue_id: VENUE_ID,
    role_groups: {
      eic: EDITORS_IN_CHIEF_ID,
      pe: PRODUCTION_EDITORS_ID
    }
  }).model.venue_context;
  var hiddenItems = [];
  var debugItems = [];
  (options.rowKeys || ['rows']).forEach(function(key) {
    if (!Array.isArray(venueStatusData[key])) return;
    var rowModel = helpers.getConsoleModel(actorContext, venueContext, roleContext, { rows: venueStatusData[key] });
    venueStatusData[key] = rowModel.model.rows || [];
    hiddenItems = hiddenItems.concat(rowModel.hidden_items || []);
    debugItems = debugItems.concat(rowModel.debug_items || []);
  });
  (options.pendingTaskKeys || []).forEach(function(key) {
    if (!Array.isArray(venueStatusData[key])) return;
    var taskModel = helpers.getConsoleModel(actorContext, venueContext, roleContext, { pending_tasks: venueStatusData[key] });
    venueStatusData[key] = taskModel.model.pending_tasks || [];
    hiddenItems = hiddenItems.concat(taskModel.hidden_items || []);
    debugItems = debugItems.concat(taskModel.debug_items || []);
  });
  venueStatusData.consoleModel = {
    role_context: roleContext,
    hidden_item_count: hiddenItems.length + debugItems.length
  };
  venueStatusData.hiddenConsoleItems = hiddenItems;
  venueStatusData.debugConsoleItems = debugItems;
  return venueStatusData;
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

var getActionEditorAssignmentPageUrl = function(submission) {
  return '/group?id=' + encodeURIComponent(VENUE_ID + '/Paper' + submission.number + '/Action_Editors') +
    '&assignAePaper=' + encodeURIComponent(submission.id || submission.forum) +
    '&assignmentInvitation=' + encodeURIComponent(VENUE_ID + '/Paper' + submission.number + '/Action_Editors/-/Assignment') +
    '&role_context=eic';
};

var getEdgeWeight = function(edge, fallback) {
  var weight = edge && edge.weight;
  return weight === undefined || weight === null ? fallback : Number(weight);
};

var getAvailabilityState = function(data) {
  return JMLRPermissionHelpers.getAssignmentAvailabilityState(data).state;
};

var getEdgesByTail = function(invitationId, head, tails) {
  var requests = tails.map(function(tail) {
    var params = { invitation: invitationId, tail: tail, domain: VENUE_ID };
    if (head) params.head = head;
    return Webfield2.api.getAll('/edges', params).then(function(edges) {
      return { tail: tail, edges: edges || [] };
    });
  });
  if (!requests.length) return $.Deferred().resolve({}).promise();

  return $.when.apply($, requests).then(function() {
    var results = requests.length === 1 ? [arguments[0]] : Array.prototype.slice.call(arguments);
    return results.reduce(function(byTail, result) {
      byTail[result.tail] = result.edges;
      return byTail;
    }, {});
  });
};

var mergeEdgesByTail = function(tails, edgeMaps) {
  tails = tails || [];
  edgeMaps = edgeMaps || [];
  return tails.reduce(function(byTail, tail) {
    byTail[tail] = edgeMaps.reduce(function(edges, edgeMap) {
      return edges.concat(edgeMap && edgeMap[tail] || []);
    }, []);
    return byTail;
  }, {});
};

var getAssignmentOpenReviewConflictEdgesByTail = function(head, tails) {
  var conflictSources = actionEditorAssignmentConflictSources();
  return $.when(
    getEdgesByTail(conflictSources.openreviewConflictInvitation, head, tails),
    getEdgesByTail(conflictSources.reviewerConflictInvitation, head, tails)
  ).then(function(actionEditorConflictsByTail, reviewerConflictsByTail) {
    return mergeEdgesByTail(tails, [actionEditorConflictsByTail, reviewerConflictsByTail]);
  });
};

var getReplies = function(submission, name, prefix) {
  return Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, name, { prefix: prefix, submissionGroupName: SUBMISSION_GROUP_NAME });
};

var getRatingInvitations = function(invitationsById, number, reviewers) {
  var invitations = [];
  var activeReviewerAnonIds = {};
  (reviewers || []).forEach(function(reviewer) {
    if (reviewer.anonId) activeReviewerAnonIds[String(reviewer.anonId)] = true;
  });
  Object.keys(invitationsById).forEach(function(invitationId) {
    var match = invitationId.match(VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Reviewer_([^/]+)/-/Rating');
    if (match && activeReviewerAnonIds[match[1]]) {
      invitations.push(invitationsById[invitationId]);
    }
  })
  return invitations;
}

var getRatingReplies = function(submission, ratingInvitations) {
  var activeRatingInvitationIds = {};
  (ratingInvitations || []).forEach(function(invitation) {
    activeRatingInvitationIds[invitation.id] = true;
  });
  var ratingReplies = submission.details.replies.filter(function(reply) {
    return activeRatingInvitationIds[reply.invitations[0]];
  });
  return ratingReplies;
}

// Main function is the entry point to the webfield code
