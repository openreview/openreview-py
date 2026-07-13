
// Helpers
var getInvitationId = function(number, name, prefix) {
  return Webfield2.utils.getInvitationId(VENUE_ID, number, name, { prefix: prefix, submissionGroupName: SUBMISSION_GROUP_NAME })
};

var getPreviousSubmissionUrl = function(submission) {
  var field = submission.content.previous_JMLR_submission_URL;
  var value = field && field.value;
  return value && value !== 'N/A' ? value : null;
};

var parsePreviousSubmissionForumId = function(url) {
  if (!url || String(url).trim().toUpperCase() === 'N/A') return null;
  var value = String(url);
  var query = value.indexOf('?') >= 0 ? value.split('?', 2)[1] : value;
  var pairs = query.split('&');
  for (var i = 0; i < pairs.length; i += 1) {
    var parts = pairs[i].split('=');
    if (parts[0] === 'id' && parts[1]) {
      try {
        return decodeURIComponent(parts[1]);
      } catch (error) {
        return parts[1];
      }
    }
  }
  var match = value.match(/forum\?id=([A-Za-z0-9_-]+)/);
  return match && match[1] || null;
};

var parsePreviousSubmissionListForumId = function(value) {
  var match = String(value || '').match(/forum\?id=([A-Za-z0-9_-]+)/);
  return match && match[1] || '';
};

var parsePreviousSubmissionListNumber = function(value) {
  var match = String(value || '').match(/Paper\s*(\d+)/i);
  return match && match[1] || '';
};

var hasPreviousSubmissionReference = function(submission) {
  var content = submission && submission.content || {};
  var previousUrl = String(getContentValue(content, 'previous_JMLR_submission_URL') || submission.previousSubmissionUrl || '').trim();
  var previousNumber = String(getContentValue(content, 'previous_JMLR_submission_number') || '').trim();
  var previousList = String(getContentValue(content, 'previous_JMLR_submissions') || '').trim();
  return (previousUrl && previousUrl.toUpperCase() !== 'N/A') ||
    (previousNumber && previousNumber.toUpperCase() !== 'N/A') ||
    !!previousList;
};

var resolvePreviousSubmissionForAssignment = function(submission) {
  var content = submission && submission.content || {};
  var previousList = String(getContentValue(content, 'previous_JMLR_submissions') || '').trim();
  var previousListForumId = parsePreviousSubmissionListForumId(previousList);
  if (previousListForumId) {
    return Webfield2.api.get('/notes', { id: previousListForumId, domain: VENUE_ID }).then(function(result) {
      return result && result.notes && result.notes[0] || null;
    }, function() {
      return null;
    });
  }

  var previousUrl = String(getContentValue(content, 'previous_JMLR_submission_URL') || submission.previousSubmissionUrl || '').trim();
  var previousForumId = parsePreviousSubmissionForumId(previousUrl);
  if (previousForumId) {
    return Webfield2.api.get('/notes', { id: previousForumId, domain: VENUE_ID }).then(function(result) {
      return result && result.notes && result.notes[0] || null;
    }, function() {
      return null;
    });
  }

  var previousNumber = String(getContentValue(content, 'previous_JMLR_submission_number') || parsePreviousSubmissionListNumber(previousList)).trim();
  if (!previousNumber || previousNumber.toUpperCase() === 'N/A' || !/^\d+$/.test(previousNumber)) {
    return $.Deferred().resolve(null).promise();
  }
  return Webfield2.api.get('/notes', {
    invitation: SUBMISSION_ID,
    number: Number(previousNumber),
    domain: VENUE_ID
  }).then(function(result) {
    return result && result.notes && result.notes[0] || null;
  }, function() {
    return null;
  });
};

var loadPreviousActionEditorAssignment = function(previousSubmission) {
  if (!previousSubmission || !previousSubmission.id) {
    return $.Deferred().resolve(null).promise();
  }
  var previousAssignmentInvitations = [
    VENUE_ID + '/Paper' + previousSubmission.number + '/Action_Editors/-/Assignment',
    ACTION_EDITOR_ID + '/-/Assignment',
    ACTION_EDITOR_ID + '/-/Archived_Assignment'
  ];
  var findAssignment = function(index) {
    if (index >= previousAssignmentInvitations.length) {
      return $.Deferred().resolve(null).promise();
    }
    return Webfield2.api.getAll('/edges', {
      invitation: previousAssignmentInvitations[index],
      head: previousSubmission.id,
      domain: VENUE_ID
    }).then(function(edges) {
      var assignment = (edges || []).find(function(edge) {
        return edge && edge.tail && !edge.ddate;
      });
      if (assignment) return assignment;
      return findAssignment(index + 1);
    }, function() {
      return findAssignment(index + 1);
    });
  };
  return findAssignment(0);
};

var decisionFieldValue = function(field) {
  return field && field.value !== undefined ? field.value : field;
};

var truthyDecisionFieldValue = function(value) {
  if (Array.isArray(value)) return value.length > 0;
  if (value === true) return true;
  if (value === false || value === null || value === undefined) return false;
  var normalized = String(value).trim().toLowerCase();
  return !!normalized && ['false', '0', 'no'].indexOf(normalized) < 0;
};

var ratingInvitationHasReviewerSelectionField = function(invitation) {
  var content = invitation && invitation.edit && invitation.edit.note && invitation.edit.note.content || {};
  return !!content.resubmission_auto_assignment;
};

var reviewerAnonIdFromRatingInvitation = function(invitationId) {
  var match = String(invitationId || '').match(/\/Reviewer_([^/]+)\/-\/Rating$/);
  return match && match[1] || '';
};

var selectedPreviousReviewerDecisionFields = function(decision) {
  var content = decision && decision.content || {};
  return Object.keys(content).filter(function(fieldName) {
    if (fieldName === 'reviewer_auto_assignment') return false;
    if (fieldName !== 'reviewers' &&
        fieldName.indexOf('reviewer_') !== 0 &&
        fieldName.indexOf('resubmission_auto_assign_reviewer_') !== 0) {
      return false;
    }
    return truthyDecisionFieldValue(decisionFieldValue(content[fieldName]));
  });
};

var loadSelectedPreviousReviewerDecisionFields = function(previousSubmission) {
  if (!previousSubmission || !previousSubmission.id || !previousSubmission.number) {
    return $.Deferred().resolve([]).promise();
  }
  return Webfield2.api.get('/notes', {
    invitation: VENUE_ID + '/Paper' + previousSubmission.number + '/-/Decision',
    forum: previousSubmission.id,
    domain: VENUE_ID
  }).then(function(result) {
    var decisions = (result && result.notes || []).filter(function(note) {
      return note && !note.ddate;
    });
    if (!decisions.length) return [];
    return selectedPreviousReviewerDecisionFields(decisions[0]);
  }, function() {
    return [];
  });
};

var resolvePreviousReviewerProfileId = function(previousSubmission, previousAnonId) {
  if (!previousSubmission || !previousSubmission.number || !previousAnonId) {
    return $.Deferred().resolve('').promise();
  }
  return Webfield2.api.get('/groups', {
    id: VENUE_ID + '/Paper' + previousSubmission.number + '/Reviewer_' + previousAnonId,
    limit: 1,
    select: 'members'
  }).then(function(result) {
    var group = result && result.groups && result.groups[0] || {};
    var members = group.members || [];
    return members[0] || '';
  }, function() {
    return '';
  });
};

var loadSelectedPreviousReviewerRatingProfiles = function(previousSubmission) {
  if (!previousSubmission || !previousSubmission.id || !previousSubmission.number) {
    return $.Deferred().resolve({ profileIds: [], hasReviewerRatingSelectionField: false }).promise();
  }
  return $.when(
    Webfield2.api.getAll('/notes', {
      forum: previousSubmission.id,
      domain: VENUE_ID
    }).then(null, function() {
      return [];
    }),
    Webfield2.api.getAll('/invitations', {
      prefix: VENUE_ID + '/Paper' + previousSubmission.number + '/Reviewer_',
      domain: VENUE_ID
    }).then(null, function() {
      return [];
    })
  ).then(function(notes, invitations) {
    var selectedProfileIds = [];
    var hasReviewerRatingSelectionField = (invitations || []).some(function(invitation) {
      return invitation && !invitation.ddate && String(invitation.id || '').indexOf('/-/Rating') >= 0 &&
        ratingInvitationHasReviewerSelectionField(invitation);
    });
    (notes || []).forEach(function(note) {
      var invitationId = note && note.invitations && note.invitations[0] || '';
      if (note.ddate || invitationId.indexOf('/-/Rating') < 0) return;
      if (!note.content || !note.content.resubmission_auto_assignment) return;
      hasReviewerRatingSelectionField = true;
      if (!truthyDecisionFieldValue(decisionFieldValue(note.content.resubmission_auto_assignment))) return;
      var profileId = decisionFieldValue(note.content.reviewer_profile_id);
      if (profileId && selectedProfileIds.indexOf(profileId) < 0) selectedProfileIds.push(profileId);
    });
    var selectedRatingNotes = (notes || []).filter(function(note) {
      var invitationId = note && note.invitations && note.invitations[0] || '';
      return !note.ddate && invitationId.indexOf('/-/Rating') >= 0 &&
        note.content && note.content.resubmission_auto_assignment &&
        truthyDecisionFieldValue(decisionFieldValue(note.content.resubmission_auto_assignment)) &&
        !decisionFieldValue(note.content.reviewer_profile_id);
    });
    return selectedRatingNotes.reduce(function(chain, note) {
      return chain.then(function(profileIds) {
        var anonId = decisionFieldValue(note.content.reviewer_anon_id) || reviewerAnonIdFromRatingInvitation(note.invitations && note.invitations[0]);
        return resolvePreviousReviewerProfileId(previousSubmission, anonId).then(function(profileId) {
          if (profileId && profileIds.indexOf(profileId) < 0) profileIds.push(profileId);
          return profileIds;
        });
      });
    }, $.Deferred().resolve(selectedProfileIds).promise()).then(function(profileIds) {
      return {
        profileIds: profileIds,
        hasReviewerRatingSelectionField: hasReviewerRatingSelectionField
      };
    });
  }, function() {
    return { profileIds: [], hasReviewerRatingSelectionField: false };
  });
};

var loadSelectedPreviousReviewerProfilesForContinuity = function(previousSubmission) {
  return loadSelectedPreviousReviewerRatingProfiles(previousSubmission).then(function(ratingSelection) {
    if (ratingSelection.hasReviewerRatingSelectionField) {
      return ratingSelection.profileIds || [];
    }
    return loadSelectedPreviousReviewerDecisionFields(previousSubmission).then(function(selectedReviewerFields) {
      return loadSelectedPreviousReviewerProfiles(previousSubmission, selectedReviewerFields);
    });
  });
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
    (typeof document !== 'undefined' && document.location) ||
    (typeof location !== 'undefined' && location);
  if (pageLocation && typeof pageLocation.reload === 'function') {
    pageLocation.reload();
  } else if (pageLocation && pageLocation.href) {
    pageLocation.href = pageLocation.href;
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
    var memberId = typeof member === 'string' ? member : member && member.id;
    return ids.indexOf(memberId) >= 0;
  });
};

var appendRoleContext = function(url, roleContext) {
  if (!url || !roleContext) return url;
  var separator = url.indexOf('?') >= 0 ? '&' : '?';
  return url + separator + 'role_context=' + encodeURIComponent(roleContext);
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

var waitForMilliseconds = function(milliseconds) {
  var deferred = $.Deferred();
  setTimeout(function() {
    deferred.resolve();
  }, milliseconds);
  return deferred.promise();
};

var SETUP_STATUS_IN_PROGRESS = 'Setup in progress';
var SETUP_STATUS_READY = 'Assignment pages created';
var SETUP_STATUS_FAILED = 'Setup failed';
var SETUP_IN_PROGRESS_TTL_MS = 60 * 60 * 1000;

var setupNoteMatchesPaper = function(setupNote, submission) {
  var content = setupNote && setupNote.content || {};
  return String(getContentValue(content, 'note_id') || '') === String(submission.id || submission.forum || '') &&
    Number(getContentValue(content, 'paper_number')) === Number(submission.number);
};

var setupReadinessMatchesPaper = function(setupNote, submission) {
  return setupNoteMatchesPaper(setupNote, submission) &&
    getContentValue(setupNote && setupNote.content || {}, 'setup_readiness_status') === SETUP_STATUS_READY;
};

var classifyAssignmentSetupNotesForPaper = function(setupNotes, submission, nowMs) {
  var matchingNotes = (setupNotes || []).filter(function(setupNote) {
    return !setupNote.ddate && setupNoteMatchesPaper(setupNote, submission);
  });
  var readyNote = null;
  var failedNote = null;
  var inProgressNote = null;
  var inProgressStartedAt = null;
  matchingNotes.forEach(function(setupNote) {
    var status = getContentValue(setupNote.content, 'setup_readiness_status');
    if (status === SETUP_STATUS_READY) readyNote = readyNote || setupNote;
    if (status === SETUP_STATUS_FAILED) failedNote = failedNote || setupNote;
    if (status === SETUP_STATUS_IN_PROGRESS) {
      var startedAt = Number(getContentValue(setupNote.content, 'setup_started_at'));
      if (startedAt && (!inProgressStartedAt || startedAt > inProgressStartedAt)) {
        inProgressNote = setupNote;
        inProgressStartedAt = startedAt;
      }
    }
  });
  var state = {
    status: 'needed',
    readyNoteId: readyNote && readyNote.id || '',
    failedNoteId: failedNote && failedNote.id || '',
    inProgressNoteId: inProgressNote && inProgressNote.id || '',
    inProgressStartedAt: inProgressStartedAt || null,
    ageMs: inProgressStartedAt ? Number(nowMs || Date.now()) - inProgressStartedAt : null
  };
  if (inProgressNote && state.ageMs < SETUP_IN_PROGRESS_TTL_MS) {
    state.status = 'in_progress';
  } else if (inProgressNote) {
    state.status = 'stale_in_progress';
  } else if (failedNote) {
    state.status = 'failed';
  }
  return state;
};

var invitationExists = function(invitationId) {
  return Webfield2.api.get('/invitations', {
    id: invitationId,
    select: 'id',
    domain: VENUE_ID
  }).then(function(result) {
    return Boolean(result && result.invitations && result.invitations.length);
  }, function() {
    return false;
  });
};

var assignmentSetupCompleteForPaper = function(submission) {
  var paperNumber = submission.number;
  return $.when(
    Webfield2.api.get('/notes', {
      invitation: VENUE_ID + '/-/Setup_Assignments',
      domain: VENUE_ID,
      limit: 100,
      sort: 'tcdate:desc'
    }).then(function(result) {
      var notes = result && result.notes || [];
      return notes.some(function(setupNote) {
        return setupReadinessMatchesPaper(setupNote, submission);
      });
    }, function() {
      return false;
    }),
    invitationExists(VENUE_ID + '/Paper' + paperNumber + '/Action_Editors/-/Assignment'),
    invitationExists(VENUE_ID + '/Paper' + paperNumber + '/Reviewers/-/Assignment'),
    invitationExists(VENUE_ID + '/Paper' + paperNumber + '/-/Assign_Action_Editor')
  ).then(function(isReady, aeInvitationExists, reviewerInvitationExists, wrapperInvitationExists) {
    return Boolean(isReady && aeInvitationExists && reviewerInvitationExists && wrapperInvitationExists);
  });
};

var waitForAssignmentSetupCompletion = function(submission, attempt, onProgress) {
  var currentAttempt = attempt || 0;
  return assignmentSetupCompleteForPaper(submission).then(function(isComplete) {
    if (isComplete) return true;
    if (currentAttempt >= 240) {
      return $.Deferred().reject('Timed out waiting for assignment pages for Paper ' + submission.number + '. Refresh the EIC console and try again.').promise();
    }
    if (onProgress) onProgress(currentAttempt + 1);
    return waitForMilliseconds(2000).then(function() {
      return waitForAssignmentSetupCompletion(submission, currentAttempt + 1, onProgress);
    });
  });
};

var setupAssignmentPagesForPaper = function(submission, onProgress) {
  return Webfield2.api.post('/notes/edits?awaitProcess=true', {
    invitation: VENUE_ID + '/-/Setup_Assignments',
    signatures: [EDITORS_IN_CHIEF_ID],
    note: {
      signatures: [EDITORS_IN_CHIEF_ID],
      content: {
        note_id: { value: submission.id },
        paper_number: { value: submission.number }
      }
    }
  }).then(function() {
    return waitForAssignmentSetupCompletion(submission, 0, onProgress);
  });
};

var getEdgeWeight = function(edge, fallback) {
  var weight = edge && edge.weight;
  return weight === undefined || weight === null ? fallback : Number(weight);
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
