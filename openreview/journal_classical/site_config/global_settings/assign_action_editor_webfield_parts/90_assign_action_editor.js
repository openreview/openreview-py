var setAutoAssignAeStatus = function(message, isError) {
  $('#auto-assign-ae-status')
    .removeClass('text-danger text-muted')
    .addClass(isError ? 'text-danger' : 'text-muted')
    .text(message || '');
};

var setActionEditorAssignmentButtonBusy = function(button) {
  if (!button || !button.length) return;
  if (!button.data('actionEditorAssignmentOriginalText')) {
    button.data('actionEditorAssignmentOriginalText', button.text());
  }
  button.prop('disabled', true);
};

var restoreActionEditorAssignmentButton = function(button) {
  if (!button || !button.length) return;
  var originalText = button.data('actionEditorAssignmentOriginalText') || button.text();
  button.prop('disabled', false).text(originalText);
  button.removeData('actionEditorAssignmentOriginalText');
};

var setActionEditorAssignmentButtonStatus = function(button, message, isError) {
  if (!button || !button.length) return;
  button.siblings('.action-editor-assignment-button-status').first()
    .text(message || '')
    .toggleClass('text-danger', !!isError)
    .toggleClass('text-success', !isError && !!message)
    .toggleClass('text-muted', !isError);
};

var setActionEditorAssignmentProgress = function(statusElement, buttonElement, message, isError) {
  if (statusElement) {
    statusElement
      .removeClass('text-danger text-muted')
      .addClass(isError ? 'text-danger' : 'text-muted')
      .text(message || '');
  }
  setActionEditorAssignmentButtonStatus(buttonElement, message, isError);
};

var formatDate = function(millis) {
  if (!millis) return '';
  var date = new Date(millis);
  if (isNaN(date.getTime())) return '';
  return date.toISOString().slice(0, 10);
};

var isOssSubmission = function(submission) {
  if (!OSS_ACTION_EDITORS_ENABLED) return false;
  return getContentValue((submission && submission.content) || {}, 'open_source_software') === true;
};

var isOssActionEditorRow = function(row) {
  return row && row.summary && row.summary.status && row.summary.status['OSS AE'] === 'Yes';
};

var actionEditorMatchesSubmissionTrack = function(row, submission) {
  if (!OSS_ACTION_EDITORS_ENABLED) return true;
  return isOssSubmission(submission) ? isOssActionEditorRow(row) : !isOssActionEditorRow(row);
};

var ACTION_EDITOR_ASSIGNMENT_RADIO_NAME = 'assign-ae-candidate';
var ASSIGN_AE_READBACK_MAX_WAIT_MS = 180000;
var ASSIGN_AE_READBACK_POLL_MS = 3000;
var ASSIGN_AE_ROLE_CONTEXT_ALLOWED = false;
var ASSIGN_AE_CONFLICT_OVERRIDE_ENABLED = false;
var getAssignedActionEditorId = function(assignedAe) {
  return assignedAe && assignedAe.id && assignedAe.id !== 'No Action Editor' ? assignedAe.id : null;
};

var getSelectedActionEditorAssignmentTail = function() {
  return $('input[name="' + ACTION_EDITOR_ASSIGNMENT_RADIO_NAME + '"]:checked').val();
};

var firstObjectFromResponse = function(response, key) {
  var collection = response && response[key];
  return collection && collection[0] || null;
};

var ACTION_EDITOR_OPENREVIEW_CONFLICT_OVERRIDE_LABEL = 'EIC OpenReview Conflict Override';

var actionEditorAssignmentOverrideLabel = function(candidate, overrideChecked) {
  if (!overrideChecked || !candidate) return undefined;
  var severity = candidate.classification && candidate.classification.severity;
  if (severity === 'author_conflict') return undefined;
  return ACTION_EDITOR_OPENREVIEW_CONFLICT_OVERRIDE_LABEL;
};

var showAssignedActionEditorReadback = function(actionEditorText) {
  if (!actionEditorText) return;
  $('#current-action-editor-name').text(actionEditorText);
  $('#current-action-editor-assignment-date').text('Just assigned');
};

var showActionEditorAssignmentComplete = function(statusElement, buttonElement, message, actionEditorText) {
  var finalMessage = (message || 'Assignment complete.').replace(/\s*Refreshing\.\.\.?\s*$/i, '');
  setActionEditorAssignmentProgress(statusElement, buttonElement, finalMessage + ' Done. Refresh the page to see current action editor assignment.', false);
  restoreActionEditorAssignmentButton(buttonElement);
  showAssignedActionEditorReadback(actionEditorText);
};

var showCurrentActionEditorRemoved = function() {
  $('#current-action-editor-name').text('None');
  $('#current-action-editor-assignment-date').text('Unknown');
  $('#current-action-editor-removal-controls').replaceWith(
    '<p class="text-muted" style="margin-bottom: 0;">No current Action Editor is assigned.</p>'
  );
};

var getActiveInvitationFromReadback = function(response) {
  var invitations = response && response.invitations || [];
  return invitations.find(function(invitation) { return invitation && invitation.id; }) || null;
};

var getActionEditorAssignmentReadbackEdges = function(submission) {
  var sources = actionEditorAssignmentReadbackSources();
  var requests = sources.map(function(sourceId) {
    return Webfield2.api.getAll('/edges', { invitation: sourceId, head: submission.id }).then(function(edges) {
      return edges || [];
    }, function() {
      return [];
    });
  });
  if (!requests.length) return $.Deferred().resolve([]).promise();
  return $.when.apply($, requests).then(function() {
    return (requests.length === 1 ? [arguments[0]] : Array.prototype.slice.call(arguments)).reduce(function(allEdges, edges) {
      return allEdges.concat(edges || []);
    }, []);
  });
};

var reviewerEntryInvitationReadback = function(invitationId) {
  return Webfield2.api.get('/invitations', { id: invitationId, select: 'id', domain: VENUE_ID }).then(getActiveInvitationFromReadback, function() {
    return null;
  });
};

var reviewerEntryGroupReadback = function(groupId) {
  return Webfield2.api.get('/groups', { id: groupId, limit: 1, select: 'id,web,content' }).then(function(result) {
    var group = result && result.groups && result.groups[0];
    var groupWeb = group && (group.web || group.content && group.content.web && group.content.web.value) || '';
    return Boolean(group && group.id && groupWeb.indexOf('AUTO_ASSIGN_CONFIG') >= 0);
  }, function() {
    return false;
  });
};

var actionEditorStageReadback = function(submission) {
  return Webfield2.api.get('/notes', { id: submission.id, domain: VENUE_ID }).then(function(result) {
    var note = result && result.notes && result.notes[0] || submission;
    var venueId = getContentValue(note && note.content || {}, 'venueid');
    return [ASSIGNED_AE_STATUS, UNDER_REVIEW_STATUS, DECISION_PENDING_STATUS].indexOf(venueId) >= 0;
  }, function() {
    var venueId = getContentValue(submission && submission.content || {}, 'venueid');
    return [ASSIGNED_AE_STATUS, UNDER_REVIEW_STATUS, DECISION_PENDING_STATUS].indexOf(venueId) >= 0;
  });
};

var waitForActionEditorAssignmentReadback = function(submission, selectedTail, startedAt) {
  var reviewerEntrySources = actionEditorReviewerEntrySources(submission);
  var elapsedMillis = Date.now() - startedAt;
  return $.when(
    actionEditorStageReadback(submission),
    getActionEditorAssignmentReadbackEdges(submission),
    reviewerEntryInvitationReadback(reviewerEntrySources.reviewerAssignmentInvitation),
    reviewerEntryGroupReadback(reviewerEntrySources.paperReviewersGroup)
  ).then(function(stageReady, activeAeEdges, reviewerAssignmentInvitation, reviewerHubReady) {
    activeAeEdges = (activeAeEdges || []).filter(function(edge) {
      return edge && !edge.ddate && edge.tail === selectedTail;
    });
    if (stageReady && activeAeEdges.some(function(edge) { return edge.tail === selectedTail; }) && reviewerAssignmentInvitation && reviewerHubReady) {
      return {
        selectedAe: selectedTail,
        assignmentEdges: activeAeEdges
      };
    }
    if (elapsedMillis >= ASSIGN_AE_READBACK_MAX_WAIT_MS) {
      return $.Deferred().reject('Action Editor assignment did not reach a complete reviewer-entry state. Waited ' + Math.round(elapsedMillis / 1000) + ' seconds.').promise();
    }
    return $.Deferred(function(deferred) {
      setTimeout(function() {
        waitForActionEditorAssignmentReadback(submission, selectedTail, startedAt).then(deferred.resolve, deferred.reject);
      }, ASSIGN_AE_READBACK_POLL_MS);
    }).promise();
  });
};

var removeActionEditorGroupMember = function(submission, actionEditorId) {
  var groupId = VENUE_ID + '/Paper' + submission.number + '/Action_Editors';
  return Webfield2.api.get('/groups', { id: groupId, limit: 1, select: 'id,members' }).then(function(result) {
    var group = result && result.groups && result.groups[0];
    var members = group && group.members || [];
    return Webfield2.api.get('/groups', {
      prefix: VENUE_ID + '/Paper' + submission.number + '/Action_Editor_',
      member: actionEditorId,
      select: 'id',
      limit: 50
    }).then(function(anonResult) {
      var anonGroupIds = (anonResult && anonResult.groups || []).map(function(anonGroup) {
        return anonGroup.id;
      }).filter(Boolean);
      var anonMembersToRemove = anonGroupIds.filter(function(anonGroupId) {
        return members.indexOf(anonGroupId) >= 0;
      });
      var membersToRemove = anonMembersToRemove.length ? anonMembersToRemove : (members.indexOf(actionEditorId) >= 0 ? [actionEditorId] : []);
      if (!membersToRemove.length) {
        return { groupId: groupId, removed: false };
      }
      return Webfield2.api.post('/groups/edits', {
        invitation: VENUE_ID + '/-/Edit',
        signatures: [VENUE_ID],
        readers: [VENUE_ID],
        writers: [VENUE_ID],
        group: {
          id: groupId,
          members: {
            remove: _.uniq(membersToRemove)
          }
        }
      }).then(function() {
        return { groupId: groupId, removed: true };
      });
    });
  });
};

var postActionEditorAssignmentRemovalEdge = function(assignmentEdge) {
  var removalBody = {
    id: assignmentEdge.id,
    invitation: assignmentEdge.invitation || actionEditorAssignmentInvitationId(),
    signatures: [EDITORS_IN_CHIEF_ID],
    head: assignmentEdge.head,
    tail: assignmentEdge.tail,
    weight: assignmentEdge.weight || 1,
    ddate: Date.now()
  };
  if (assignmentEdge.label) removalBody.label = assignmentEdge.label;
  return Webfield2.api.post('/edges?awaitProcess=true', removalBody);
};

var postCurrentActionEditorRemoval = function(submission, assignedAe, assignmentEdge, statusElement, buttonElement) {
  var currentAeId = getAssignedActionEditorId(assignedAe);
  if (!currentAeId) {
    setActionEditorAssignmentProgress(statusElement, buttonElement, 'No current Action Editor was found to remove.', true);
    restoreActionEditorAssignmentButton(buttonElement);
    return $.Deferred().reject('No current Action Editor was found to remove.').promise();
  }
  if (!assignmentEdge || !assignmentEdge.id) {
    return removeActionEditorGroupMember(submission, currentAeId).then(function() {
      setActionEditorAssignmentProgress(statusElement, buttonElement, 'Removed stale current Action Editor group membership. Done. Refresh the page to assign another Action Editor.', false);
      showCurrentActionEditorRemoved();
      restoreActionEditorAssignmentButton(buttonElement);
    }).fail(function(error) {
      var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to remove the stale current Action Editor group membership.';
      setActionEditorAssignmentProgress(statusElement, buttonElement, message, true);
      restoreActionEditorAssignmentButton(buttonElement);
    });
  }
  return postActionEditorAssignmentRemovalEdge(assignmentEdge).then(function() {
    setActionEditorAssignmentProgress(statusElement, buttonElement, 'Removed current Action Editor. Done. Refresh the page to assign another Action Editor.', false);
    showCurrentActionEditorRemoved();
    restoreActionEditorAssignmentButton(buttonElement);
  }).fail(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to remove the current Action Editor.';
    setActionEditorAssignmentProgress(statusElement, buttonElement, message, true);
    restoreActionEditorAssignmentButton(buttonElement);
  });
};

var postSelectedActionEditorAssignment = function(submission, selectedTail, statusElement, buttonElement, fallbackMessage, edgeLabel, assignedAe) {
  if (!ASSIGN_AE_ROLE_CONTEXT_ALLOWED) {
    var roleContextMessage = 'Open this page from the editor-in-chief role context to assign an action editor.';
    setActionEditorAssignmentProgress(statusElement, buttonElement, roleContextMessage, true);
    restoreActionEditorAssignmentButton(buttonElement);
    return $.Deferred().reject(roleContextMessage).promise();
  }
  if (!selectedTail) return $.Deferred().reject('Select one action editor to assign.').promise();
  var currentAeId = getAssignedActionEditorId(assignedAe);
  if (currentAeId && currentAeId !== selectedTail) {
    var currentAeMessage = 'Unassign the current Action Editor before assigning another.';
    setActionEditorAssignmentProgress(statusElement, buttonElement, currentAeMessage, true);
    restoreActionEditorAssignmentButton(buttonElement);
    return $.Deferred().reject(currentAeMessage).promise();
  }
  var postBody = {
    invitation: actionEditorAssignmentInvitationId(),
    signatures: [EDITORS_IN_CHIEF_ID],
    head: submission.id,
    tail: selectedTail,
    weight: 1
  };
  if (edgeLabel) postBody.label = edgeLabel;
  return Webfield2.api.post('/edges?awaitProcess=true', postBody).then(function() {
    setActionEditorAssignmentProgress(statusElement, buttonElement, 'Assignment posted. Confirming action editor and reviewer-entry readiness...', false);
    return waitForActionEditorAssignmentReadback(submission, selectedTail, Date.now());
  }).fail(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || fallbackMessage || 'Unable to assign the selected action editor.';
    setActionEditorAssignmentProgress(statusElement, buttonElement, message, true);
    restoreActionEditorAssignmentButton(buttonElement);
  });
};

var parsePreviousSubmissionForumId = function(url) {
  if (!url || String(url).trim().toUpperCase() === 'N/A') return null;
  try {
    var baseUrl = typeof location !== 'undefined' && location.origin ? location.origin : null;
    var parsed = baseUrl ? new URL(String(url), baseUrl) : new URL(String(url));
    return parsed.searchParams.get('id');
  } catch (error) {
    try {
      return String(url).split('forum?id=')[1].split('&')[0] || null;
    } catch (innerError) {
      return null;
    }
  }
};

var parsePreviousSubmissionListForumId = function(value) {
  var match = String(value || '').match(/forum\?id=([A-Za-z0-9_-]+)/);
  return match && match[1] || null;
};

var parsePreviousSubmissionListNumber = function(value) {
  var match = String(value || '').match(/Paper\s+([0-9]+)/);
  return match && match[1] || '';
};

var hasPreviousSubmissionReference = function(submission) {
  var content = submission && submission.content || {};
  var previousUrl = String(content.previous_JMLR_submission_URL || submission.previousSubmissionUrl || '').trim();
  var previousNumber = String(content.previous_JMLR_submission_number || '').trim();
  var previousList = String(content.previous_JMLR_submissions || '').trim();
  return (previousUrl && previousUrl.toUpperCase() !== 'N/A') ||
    (previousNumber && previousNumber.toUpperCase() !== 'N/A') ||
    !!previousList;
};

var resolvePreviousSubmissionForAssignment = function(submission) {
  var content = submission && submission.content || {};
  var previousList = String(content.previous_JMLR_submissions || '').trim();
  var previousListForumId = parsePreviousSubmissionListForumId(previousList);
  if (previousListForumId) {
    return Webfield2.api.get('/notes', { id: previousListForumId }).then(function(result) {
      return result && result.notes && result.notes[0] || null;
    }, function() {
      return null;
    });
  }

  var previousUrl = String(content.previous_JMLR_submission_URL || submission.previousSubmissionUrl || '').trim();
  var previousForumId = parsePreviousSubmissionForumId(previousUrl);
  if (previousForumId) {
    return Webfield2.api.get('/notes', { id: previousForumId }).then(function(result) {
      return result && result.notes && result.notes[0] || null;
    }, function() {
      return null;
    });
  }

  var previousNumber = String(content.previous_JMLR_submission_number || parsePreviousSubmissionListNumber(previousList)).trim();
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
  var previousAssignmentInvitations = actionEditorAssignmentLoadSources().assignmentHistorySources;
  var previousPaperAssignmentInvitation = VENUE_ID + '/Paper' + previousSubmission.number + '/Action_Editors/-/Assignment';
  if (previousAssignmentInvitations.indexOf(previousPaperAssignmentInvitation) < 0) {
    previousAssignmentInvitations = [previousPaperAssignmentInvitation].concat(previousAssignmentInvitations);
  }
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
      if (assignment) {
        return assignment;
      }
      return findAssignment(index + 1);
    }, function() {
      return findAssignment(index + 1);
    });
  };
  return findAssignment(0);
};

var renderPreviousActionEditorAssignment = function(submission, assignedAe, actionEditorRows) {
  var button = $('#show-previous-action-editor');
  var panel = $('#previous-ae-assignment-section');
  var status = $('#previous-ae-assignment-status');
  if (!button.length || !panel.length) return;

  if (!hasPreviousSubmissionReference(submission)) {
    button.hide();
    panel.hide();
    return;
  }

  button.show().prop('disabled', true).text('Previous AE');
  status.removeClass('text-danger').addClass('text-muted').text('Looking up previous action editor...');

  resolvePreviousSubmissionForAssignment(submission).then(function(previousSubmission) {
    if (!previousSubmission) {
      status.removeClass('text-muted').addClass('text-danger').text('No previous JMLR submission could be resolved.');
      return null;
    }
    return loadPreviousActionEditorAssignment(previousSubmission).then(function(previousAssignment) {
      return {
        previousSubmission: previousSubmission,
        previousAssignment: previousAssignment
      };
    });
  }).then(function(result) {
    if (!result) return;
    var previousSubmission = result.previousSubmission;
    var previousAssignment = result.previousAssignment;
    if (!previousAssignment || !previousAssignment.tail) {
      status.removeClass('text-muted').addClass('text-danger').text('No previous action editor assignment was found for Paper ' + previousSubmission.number + '.');
      return;
    }

    var previousAeId = previousAssignment.tail;
    var previousAeRow = (actionEditorRows || []).find(function(row) {
      return row && row.summary && row.summary.id === previousAeId;
    });
    var previousAeName = previousAeRow && previousAeRow.summary && previousAeRow.summary.name || previousAeId;
    var currentAeId = assignedAe && assignedAe.id && assignedAe.id !== 'No Action Editor' ? assignedAe.id : null;
    var alreadyAssigned = currentAeId === previousAeId;
    var blockedByCurrentActionEditor = currentAeId && !alreadyAssigned;
    var activePaperLoad = previousAeRow && previousAeRow.reviewProgressData && previousAeRow.reviewProgressData.numPapers || 0;
    var isOssActionEditor = isOssActionEditorRow(previousAeRow);
    var maxPapers = (OSS_ACTION_EDITORS_ENABLED && isOssActionEditor) ? OSS_ACTION_EDITORS_MAX_PAPERS : ACTION_EDITORS_DEFAULT_MAX_PAPERS;
    var classification = previousAeRow
      ? classifyActionEditorCandidate(submission, previousAeRow, {
        id: previousAeId,
        activePaperLoad: activePaperLoad,
        maxPapers: maxPapers,
        current: alreadyAssigned,
        active: !(previousAeRow.summary && previousAeRow.summary.status && previousAeRow.summary.status.Active !== 'Active')
      })
      : JMLRPermissionHelpers.classifyAssignmentCandidate(submission, { id: previousAeId, tail: previousAeId }, { role: 'action_editor' });
    var loadWarning = activePaperLoad >= maxPapers;
    var authorConflict = classification.conflict && classification.conflict.kind === 'author_conflict';
    var conflictWarning = classification.conflict && classification.conflict.kind === 'openreview_positive';
    var unavailableWarning = classification.availability && classification.availability.state !== 'available';
    var warningItems = [];
    (classification.conflict && classification.conflict.reasons || []).forEach(function(reason) {
      warningItems.push(reason.label + '.');
    });
    if (loadWarning) warningItems.push('Active paper load is ' + activePaperLoad + ' / ' + maxPapers + '; continuity reassignment bypasses this load warning.');
    if (unavailableWarning) {
      warningItems.push(classification.availability.state === 'until'
        ? classification.availability.label + '; continuity reassignment bypasses this availability warning.'
        : 'Marked unavailable indefinitely; continuity reassignment bypasses this availability warning.');
    }
    var warningMarkup = warningItems.length
      ? '<div class="alert ' + (authorConflict ? 'alert-danger' : 'alert-warning') + '" style="margin-top: 10px;">' +
          '<p><strong>Continuity warnings</strong></p>' +
          '<ul>' + warningItems.map(function(item) { return '<li>' + _.escape(item) + '</li>'; }).join('') + '</ul>' +
          '<p style="margin-bottom: 0;">' + _.escape(authorConflict ? 'Author-list and author-declared conflict-list matches are hard conflicts and cannot be bypassed here.' : 'These warnings are shown for review. Assign Previous AE can bypass OpenReview conflicts only because this person was assigned to the immediate previous submission.') + '</p>' +
        '</div>'
      : '<p class="text-muted">No conflict, load, or availability warnings were found for this previous action editor.</p>';
    var conflictOverrideMarkup = authorConflict
      ? '<p class="text-danger">This previous action editor is blocked by a hard author conflict.</p>'
      :
      '<div class="checkbox"><label><input id="include-conflicted-previous-action-editor" type="checkbox"> ' +
      (conflictWarning
        ? 'Assign despite the OpenReview conflict warning and record a previous-AE conflict override.'
        : 'If OpenReview reports a conflict at submit time, record a previous-AE conflict override.') +
      '</label></div>';

    button.prop('disabled', false);
    status.removeClass('text-danger').addClass('text-muted').text('');
    panel.html(
      '<div class="panel panel-default" style="margin-top: 12px;">' +
        '<div class="panel-heading"><strong>Previous action editor</strong></div>' +
        '<div class="panel-body">' +
          '<p><strong>Previous paper:</strong> Paper ' + _.escape(String(previousSubmission.number)) + '</p>' +
          '<p><strong>Previous AE:</strong> ' + _.escape(previousAeName) + ' <span class="text-muted">' + _.escape(previousAeId) + '</span></p>' +
          '<p><strong>Track:</strong> ' + _.escape(isOssActionEditor ? 'OSS AE' : 'Regular AE') + '</p>' +
          '<p><strong>Active paper load:</strong> ' + _.escape(String(activePaperLoad)) + ' / ' + _.escape(String(maxPapers)) + '</p>' +
          warningMarkup +
          conflictOverrideMarkup +
          '<p class="text-muted">Assignment is submitted through the normal action-editor assignment process. For continuity reassignment, load and availability are warnings; OpenReview conflicts can be overridden only with the recorded checkbox above.</p>' +
          '<button id="assign-previous-action-editor" type="button" class="btn btn-primary"' + (alreadyAssigned || blockedByCurrentActionEditor || authorConflict || conflictWarning ? ' disabled' : '') + '>' +
            (alreadyAssigned ? 'Previous AE already assigned' : (blockedByCurrentActionEditor ? 'Unassign current AE first' : 'Assign Previous AE')) +
          '</button>' +
          '<span class="action-editor-assignment-button-status text-muted" style="margin-left: 8px;"></span>' +
          '<p id="assign-previous-ae-status" class="text-muted" style="margin-top: 8px;"></p>' +
        '</div>' +
      '</div>'
    ).show();

    button.off('click').on('click', function() {
      $('#manual-ae-search-section').hide();
      $('#confirm-auto-assign-ae-container').remove();
      panel.show();
      var panelNode = panel[0];
      if (panelNode && panelNode.scrollIntoView) panelNode.scrollIntoView({ block: 'start' });
    });

    $('#include-conflicted-previous-action-editor').off('change').on('change', function() {
      $('#assign-previous-action-editor').prop('disabled', alreadyAssigned || blockedByCurrentActionEditor || authorConflict || (conflictWarning && !$(this).prop('checked')));
    });

    $('#assign-previous-action-editor').off('click').on('click', function() {
      var assignButton = $(this);
      var assignStatus = $('#assign-previous-ae-status');
      var includeConflictOverride = $('#include-conflicted-previous-action-editor').prop('checked');
      if (authorConflict) {
        setActionEditorAssignmentProgress(assignStatus, assignButton, 'This previous action editor is blocked by an author conflict.', true);
        return;
      }
      if (conflictWarning && !includeConflictOverride) {
        setActionEditorAssignmentProgress(assignStatus, assignButton, 'Confirm the conflict override before assigning the previous action editor.', true);
        return;
      }
      setActionEditorAssignmentButtonBusy(assignButton);
      postSelectedActionEditorAssignment(
        submission,
        previousAeId,
        assignStatus,
        assignButton,
        'Unable to assign the previous action editor.',
        includeConflictOverride ? 'Previous AE Conflict Override' : undefined,
        assignedAe
      ).then(function() {
        showActionEditorAssignmentComplete(assignStatus, assignButton, 'Assigned previous action editor. Refreshing...', previousAeName);
      });
    });
  });
};

var filterActionEditorRowsForSubmission = function(submission, actionEditorRows) {
  return (actionEditorRows || []).filter(function(row) {
    return row && row.summary && row.summary.id && actionEditorMatchesSubmissionTrack(row, submission);
  });
};

var COMMON_PERSONAL_EMAIL_DOMAINS = {
  'gmail.com': true,
  'googlemail.com': true,
  'hotmail.com': true,
  'outlook.com': true,
  'live.com': true,
  'icloud.com': true,
  'me.com': true,
  'mac.com': true,
  'yahoo.com': true,
  'proton.me': true,
  'protonmail.com': true
};

var normalizeAssignmentConflictText = function(value) {
  return String(value || '').trim().toLowerCase();
};

var extractAssignmentEmails = function(text) {
  var matches = String(text || '').match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/ig) || [];
  return _.uniq(matches.map(function(email) {
    return email.toLowerCase();
  }));
};

var extractAssignmentProfileIds = function(values) {
  return _.uniq((values || []).reduce(function(ids, value) {
    String(value || '').split(/[\s,;|()[\]<>]+/).forEach(function(token) {
      if (/^~[A-Za-z0-9_]+[0-9]*$/.test(token)) ids.push(token);
    });
    return ids;
  }, []));
};

var getEmailDomain = function(email) {
  var parts = String(email || '').toLowerCase().split('@');
  return parts.length === 2 ? parts[1] : '';
};

var getProfileContent = function(profile) {
  return profile && profile.content || {};
};

var getProfileEmails = function(profile) {
  var content = getProfileContent(profile);
  return _.uniq([content.preferredEmail].concat(content.emails || [], content.emailsConfirmed || []).filter(Boolean).map(function(email) {
    return String(email).toLowerCase();
  }));
};

var getProfileDomains = function(profile) {
  var content = getProfileContent(profile);
  var emailDomains = getProfileEmails(profile).map(getEmailDomain).filter(Boolean);
  var historyDomains = (content.history || []).map(function(item) {
    return item && item.institution && item.institution.domain;
  }).filter(Boolean).map(function(domain) {
    return String(domain).toLowerCase();
  });
  return _.uniq(emailDomains.concat(historyDomains).filter(function(domain) {
    return domain && !COMMON_PERSONAL_EMAIL_DOMAINS[domain];
  }));
};

var getCandidateProfileModel = function(rowOrCandidate) {
  var summary = rowOrCandidate && rowOrCandidate.summary || rowOrCandidate || {};
  var content = Object.assign({}, summary.profileContent || {});
  content.emails = _.uniq((content.emails || []).concat(summary.allEmails || [], summary.email ? [summary.email] : []));
  return {
    content: content
  };
};

var getBrowserComputedActionEditorConflictReasons = function(submission, rowOrCandidate) {
  var model = submission && submission.browserConflictModel || getSubmissionBrowserConflictModel(submission);
  var profile = getCandidateProfileModel(rowOrCandidate);
  var candidateEmails = getProfileEmails(profile);
  var candidateDomains = getProfileDomains(profile);
  var emailMatches = candidateEmails.filter(function(email) {
    return model.emails.indexOf(email) >= 0;
  });
  var domainMatches = candidateDomains.filter(function(domain) {
    return model.domains.indexOf(domain) >= 0;
  });
  if (!emailMatches.length && !domainMatches.length) return [];
  return [{
    code: 'openreview_positive',
    label: 'OpenReview-computed conflict'
  }];
};

var assignmentConflictRejectedByBackend = function(errorOrMessage) {
  var message = typeof errorOrMessage === 'string'
    ? errorOrMessage
    : errorOrMessage && errorOrMessage.responseJSON && errorOrMessage.responseJSON.message || errorOrMessage && errorOrMessage.message || '';
  return /Can not add assignment, conflict detected for/i.test(message);
};

var extractOnDemandAssignmentAffinityScore = function(results, noteId, tail) {
  var rows = [];
  var collectRows = function(value) {
    if (!value) return;
    if (Array.isArray(value)) {
      value.forEach(collectRows);
      return;
    }
    if (typeof value === 'object') {
      rows.push(value);
      Object.keys(value).forEach(function(key) {
        if (key !== 'publication' && key !== 'profile') collectRows(value[key]);
      });
    }
  };
  collectRows(results);
  for (var index = 0; index < rows.length; index += 1) {
    var row = rows[index] || {};
    var rowNoteId = row.submission || row.submission_id || row.submissionId || row.paper || row.paper_id || row.paperId || row.forum || row.note || row.note_id || row.noteId || row.head || row.entityB || row.id;
    if (rowNoteId && typeof rowNoteId === 'object') rowNoteId = rowNoteId.id || rowNoteId.forum || rowNoteId.noteId;
    if (rowNoteId === noteId) {
      var scoreMap = row.scores || row.scoreByUser || row.userScores || row.members || row.users;
      if (scoreMap && scoreMap[tail] !== undefined && !isNaN(Number(scoreMap[tail]))) return Number(scoreMap[tail]);
    }
    var rowTail = row.user || row.user_id || row.userId || row.profile || row.profile_id || row.profileId || row.member || row.member_id || row.memberId || row.tail || row.entityA;
    if (rowTail && typeof rowTail === 'object') rowTail = rowTail.id || rowTail.profile_id || rowTail.user;
    var score = row.score || row.weight || row.value || row.similarity;
    if (rowNoteId === noteId && rowTail === tail && score !== undefined && !isNaN(Number(score))) return Number(score);
  }
  return null;
};

var requestOnDemandAssignmentAffinity = function(options) {
  options = options || {};
  if (!options.tail || !options.invitationId || !options.groupId || !options.noteId) {
    return $.Deferred().resolve({ tail: options.tail, score: null, missing: true }).promise();
  }
  var jobName = [
    'jmlr',
    VENUE_ID.replace(/\//g, '-'),
    options.role || 'assignment',
    'affinity',
    'paper' + (options.paperNumber || 'unknown'),
    options.tail.replace(/[^A-Za-z0-9_~.-]/g, ''),
    Date.now()
  ].join('-');
  var payload = {
    name: jobName,
    entityA: {
      type: 'Group',
      reviewerIds: [options.tail]
    },
    entityB: {
      type: 'Note',
      submissions: [{
        id: options.noteId,
        title: options.title || '',
        abstract: options.abstract || ''
      }]
    },
    model: {
      name: EXPERTISE_MODEL || 'specter2+scincl',
      normalizeScores: false
    }
  };
  return Webfield2.api.post('/expertise', payload).then(function(response) {
    var jobId = response && (response.jobId || response.job_id || response.id);
    if (!jobId) return { tail: options.tail, score: null, missing: true };
    return Webfield2.api.get('/expertise/status', { jobId: jobId }).then(function(statusResponse) {
      if (statusResponse && statusResponse.status && statusResponse.status !== 'Completed') {
        return { tail: options.tail, score: null, missing: true, jobId: jobId, status: statusResponse.status };
      }
      return Webfield2.api.get('/expertise/results', { jobId: jobId }).then(function(results) {
        var score = extractOnDemandAssignmentAffinityScore(results, options.noteId, options.tail);
        if (score === null) return { tail: options.tail, score: null, missing: true, jobId: jobId };
        return Webfield2.api.getAll('/edges', {
          invitation: options.invitationId,
          head: options.noteId,
          tail: options.tail,
          domain: VENUE_ID
        }).then(function(existingEdges) {
          var activeEdge = (existingEdges || []).filter(function(edge) { return edge && !edge.ddate; })[0] || null;
          var edgePayload = {
            invitation: options.invitationId,
            signatures: [VENUE_ID],
            head: options.noteId,
            tail: options.tail,
            weight: score
          };
          if (activeEdge && activeEdge.id) edgePayload.id = activeEdge.id;
          return Webfield2.api.post('/edges', edgePayload).then(function() {
            return { tail: options.tail, score: score, missing: false, jobId: jobId };
          }, function() {
            return { tail: options.tail, score: score, missing: false, jobId: jobId };
          });
        });
      });
    });
  }, function() {
    return { tail: options.tail, score: null, missing: true };
  });
};

var materializeOnDemandAssignmentConflict = function(options) {
  options = options || {};
  if (!options.tail || !options.signature || !options.submission || !options.submission.id) {
    return $.Deferred().reject({ message: 'Missing assignment candidate conflict refresh inputs.' }).promise();
  }
  var conflictSources = actionEditorAssignmentConflictSources();
  return Webfield2.api.post('/notes/edits?awaitProcess=true', {
    invitation: conflictSources.candidateRefreshInvitation,
    signatures: [options.signature],
    note: {
      content: {
        note_id: { value: options.submission.id },
        paper_number: { value: options.submission.number },
        candidate_id: { value: options.tail }
      }
    }
  });
};

var markCandidateBackendOpenReviewConflict = function(submission, candidate) {
  if (!candidate) return candidate;
  var existingReasons = candidate.classification && candidate.classification.conflict && candidate.classification.conflict.reasons || [];
  var conflictReasons = existingReasons.concat([{
    code: 'openreview_positive',
    label: 'OpenReview conflict detected by backend'
  }]);
  candidate.classification = JMLRPermissionHelpers.classifyAssignmentCandidate(submission, {
    id: candidate.id || candidate.tail,
    tail: candidate.tail || candidate.id,
    conflictReasons: conflictReasons,
    activePaperLoad: candidate.activePaperLoad,
    maxPapers: candidate.maxPapers,
    cooldown_until: candidate.cooldownUntil || candidate.cooldown_until,
    assigned: candidate.assigned,
    current: candidate.assigned,
    active: true
  }, { role: 'action_editor' });
  candidate.eligible = candidate.classification.eligible;
  return candidate;
};

var actionEditorCandidateInput = function(submission, row, options) {
  options = options || {};
  var summary = row && row.summary || {};
  return {
    id: options.id || summary.id,
    tail: options.id || summary.id,
    name: summary.name || options.id || summary.id,
    email: summary.email || '',
    allEmails: summary.allEmails || [],
    institution: summary.institution || '',
    conflictEdge: options.conflictEdge || row && row.conflictData,
    conflictReasons: options.conflictReasons || row && row.browserConflictReasons,
    availabilityEdge: options.availabilityEdge || row && row.availabilityData,
    availabilityData: options.availabilityData || options.availabilityEdge || row && row.availabilityData,
    activePaperLoad: options.activePaperLoad,
    maxPapers: options.maxPapers,
    cooldown_until: options.cooldownUntil || options.cooldown_until,
    assigned: options.assigned,
    current: options.current,
    active: options.active !== undefined ? options.active : !(summary.status && summary.status.Active !== 'Active'),
    blockers: options.blockers || []
  };
};

var loadSubmissionAuthorProfiles = function(submission) {
  var authorIds = _.uniq((submission && submission.content && submission.content.authorids || []).filter(function(authorId) {
    return String(authorId || '').indexOf('~') === 0;
  }));
  if (!authorIds.length) return $.Deferred().resolve([]).promise();
  return Webfield2.api.post('/profiles/search', { ids: authorIds }).then(function(result) {
    return result && result.profiles || [];
  }, function() {
    return [];
  });
};

var getSubmissionBrowserConflictModel = function(submission) {
  var content = submission && submission.content || {};
  var authorIds = Array.isArray(content.authorids) ? content.authorids : [];
  var authorListText = content.author_list || '';
  var conflictText = content.conflict_of_interests || '';
  var authorProfiles = submission && submission.authorProfiles || [];
  var profileEmails = _.uniq(authorProfiles.reduce(function(emails, profile) {
    return emails.concat(getProfileEmails(profile));
  }, []));
  var profileDomains = _.uniq(authorProfiles.reduce(function(domains, profile) {
    return domains.concat(getProfileDomains(profile));
  }, []));
  var combinedText = [authorIds.join(' '), authorListText, conflictText].join('\n');
  var emails = _.uniq(extractAssignmentEmails(combinedText).concat(profileEmails));
  var domains = _.uniq(emails.map(getEmailDomain).concat(profileDomains).filter(function(domain) {
    return domain && !COMMON_PERSONAL_EMAIL_DOMAINS[domain];
  }));
  return {
    text: normalizeAssignmentConflictText(combinedText),
    profileIds: extractAssignmentProfileIds(authorIds.concat([authorListText, conflictText])),
    emails: emails,
    domains: domains,
    institutionDomains: institutionDomains || []
  };
};

var getActionEditorBrowserConflictReasons = function(submission, row) {
  var reasons = JMLRPermissionHelpers.getCandidateAssignmentConflictReasons(
    submission,
    actionEditorCandidateInput(submission, row, {})
  );
  return reasons
    .filter(function(reason) { return reason.code !== 'openreview_positive' && reason.code !== 'openreview_conflict_edge'; })
    .map(function(reason) { return reason.label; });
};

var classifyActionEditorCandidate = function(submission, row, options) {
  return JMLRPermissionHelpers.classifyAssignmentCandidate(
    submission,
    actionEditorCandidateInput(submission, row, options),
    { role: 'action_editor' }
  );
};

var getActionEditorCooldownUntil = function(assignmentEdges, currentPaperId) {
  return JMLRPermissionHelpers.getAssignmentCooldownUntil(
    assignmentEdges,
    currentPaperId,
    ACTION_EDITOR_NEW_ASSIGNMENT_COOLDOWN_DAYS
  );
};

var isActionEditorAssignmentHistoryEdge = function(edge) {
  var invitationId = edge && edge.invitation || '';
  var assignmentHistorySources = actionEditorAssignmentLoadSources().assignmentHistorySources;
  return assignmentHistorySources.indexOf(invitationId) >= 0 ||
    (invitationId.indexOf(VENUE_ID + '/Paper') === 0 && /\/Action_Editors\/-\/Assignment$/.test(invitationId));
};

var mergeAssignmentHistoryEdges = function(primaryEdges, supplementalEdges) {
  var seen = {};
  return (primaryEdges || []).concat(supplementalEdges || []).filter(function(edge) {
    var key = edge && (edge.id || [edge.invitation, edge.head, edge.tail, edge.cdate].join('|'));
    if (!key || seen[key]) return false;
    seen[key] = true;
    return true;
  });
};

var recentActionEditorAssignmentQueries = function(submissionRows, activePaperIdsByHead, currentPaperId) {
  var now = Date.now();
  var cooldownMillis = Number(ACTION_EDITOR_NEW_ASSIGNMENT_COOLDOWN_DAYS || 0) * 24 * 60 * 60 * 1000;
  var cutoff = cooldownMillis ? now - cooldownMillis : now;
  var queryKeys = {};
  var queries = [];
  (submissionRows || []).forEach(function(row) {
    var note = row && row.submission || {};
    if (!note.number || !note.id) return;
    var createdAt = Number(note.cdate || note.tcdate || 0);
    if (note.id !== currentPaperId && !activePaperIdsByHead[note.id] && (!createdAt || createdAt < cutoff)) return;
    var invitationId = VENUE_ID + '/Paper' + note.number + '/Action_Editors/-/Assignment';
    var key = invitationId + '|' + note.id;
    if (queryKeys[key]) return;
    queryKeys[key] = true;
    queries.push({ invitation: invitationId, head: note.id });
  });
  return queries;
};

var getRecentActionEditorAssignmentEdgesByTail = function(submissionRows, activePaperIdsByHead, currentPaperId) {
  var queries = recentActionEditorAssignmentQueries(submissionRows, activePaperIdsByHead || {}, currentPaperId);
  if (!queries.length) return $.Deferred().resolve({}).promise();
  var requests = queries.map(function(query) {
    return Webfield2.api.getAll('/edges', { invitation: query.invitation, head: query.head, domain: VENUE_ID }).then(function(edges) {
      return edges || [];
    }, function() {
      return [];
    });
  });
  return $.when.apply($, requests).then(function() {
    var results = requests.length === 1 ? [arguments[0]] : Array.prototype.slice.call(arguments);
    return results.reduce(function(byTail, edges) {
      (edges || []).forEach(function(edge) {
        if (!edge || !edge.tail || !isActionEditorAssignmentHistoryEdge(edge)) return;
        byTail[edge.tail] = byTail[edge.tail] || [];
        byTail[edge.tail].push(edge);
      });
      return byTail;
    }, {});
  });
};

var getActionEditorAssignmentHistoryByTail = function(tails, supplementalEdgesByTail) {
  supplementalEdgesByTail = supplementalEdgesByTail || {};
  var requests = tails.map(function(tail) {
    return Webfield2.api.getAll('/edges', { tail: tail, domain: VENUE_ID }).then(function(edges) {
      return {
        tail: tail,
        edges: mergeAssignmentHistoryEdges(
          (edges || []).filter(isActionEditorAssignmentHistoryEdge),
          supplementalEdgesByTail[tail] || []
        )
      };
    }, function() {
      return {
        tail: tail,
        edges: mergeAssignmentHistoryEdges([], supplementalEdgesByTail[tail] || [])
      };
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

var getDecisionCompletedPaperIdsByHead = function(submissionRows) {
  return (submissionRows || []).reduce(function(byHead, row) {
    var submission = row && row.submission || {};
    var actionEditorProgressData = row && row.actionEditorProgressData || {};
    if (submission.id && actionEditorProgressData.metaReview) byHead[submission.id] = true;
    return byHead;
  }, {});
};

var getActionEditorActiveAssignmentLoad = function(assignmentEdges, currentPaperId, decisionCompletedPaperIdsByHead) {
  decisionCompletedPaperIdsByHead = decisionCompletedPaperIdsByHead || {};
  var activeHeads = {};
  (assignmentEdges || []).forEach(function(edge) {
    if (!edge || edge.ddate || !edge.head) return;
    if (edge.head === currentPaperId) return;
    if (decisionCompletedPaperIdsByHead[edge.head]) return;
    activeHeads[edge.head] = true;
  });
  return Object.keys(activeHeads).length;
};

var getActiveActionEditorPaperIdsByHead = function(actionEditorRows) {
  return (actionEditorRows || []).reduce(function(byHead, row) {
    var papers = row.reviewProgressData && row.reviewProgressData.papers || [];
    papers.forEach(function(paper) {
      var note = paper && paper.note || {};
      var head = note.id || note.forum;
      if (head) byHead[head] = true;
    });
    return byHead;
  }, {});
};

var buildActionEditorAssignmentCandidate = function(submission, row, assignedAe, factsByTail, options) {
  factsByTail = factsByTail || {};
  options = options || {};
  var summary = row.summary || {};
  var tail = summary.id;
  var currentAeId = assignedAe && assignedAe.id && assignedAe.id !== 'No Action Editor' ? assignedAe.id : null;
  var assigned = tail === currentAeId || tail === options.assignedTail;
  var assignmentHistory = (factsByTail.assignmentHistoryByTail && factsByTail.assignmentHistoryByTail[tail]) || [];
  var availabilityEdge = (factsByTail.availabilityByTail && factsByTail.availabilityByTail[tail] || [])[0] || row.availabilityData;
  var customMaxEdge = (factsByTail.maxPapersByTail && factsByTail.maxPapersByTail[tail] || [])[0];
  var cooldownUntil = getActionEditorCooldownUntil(assignmentHistory, submission.id);
  var availabilityState = getAvailabilityState(availabilityEdge);
  var isOssActionEditor = isOssActionEditorRow(row);
  var maxPapers = isOssActionEditor ? options.ossActionEditorsMaxPapers : (customMaxEdge ? getEdgeWeight(customMaxEdge, ACTION_EDITORS_DEFAULT_MAX_PAPERS) : ACTION_EDITORS_DEFAULT_MAX_PAPERS);
  var activePaperLoad = getActionEditorActiveAssignmentLoad(
    assignmentHistory,
    submission.id,
    factsByTail.decisionCompletedPaperIdsByHead
  );
  var conflictEdge = (factsByTail.conflictsByTail && factsByTail.conflictsByTail[tail] || [])[0];
  var browserComputedConflictReasons = getBrowserComputedActionEditorConflictReasons(submission, row);
  var affinityByTail = factsByTail.affinityByTail || {};
  var hasAffinity = affinityByTail[tail] !== undefined;
  var classification = classifyActionEditorCandidate(submission, row, {
    id: tail,
    conflictEdge: conflictEdge,
    conflictReasons: browserComputedConflictReasons,
    availabilityEdge: availabilityEdge,
    availabilityData: availabilityEdge,
    activePaperLoad: activePaperLoad,
    maxPapers: maxPapers,
    cooldownUntil: cooldownUntil,
    assigned: assigned,
    current: tail === currentAeId,
    active: !(summary.status && summary.status.Active !== 'Active')
  });
  return {
    id: tail,
    tail: tail,
    name: summary.name || tail,
    email: summary.email || '',
    allEmails: summary.allEmails || [],
    profileContent: summary.profileContent || {},
    institution: summary.institution || '',
    assigned: assigned,
    active: !(summary.status && summary.status.Active !== 'Active'),
    isOssActionEditor: isOssActionEditor,
    track: isOssActionEditor ? 'OSS AE' : 'Regular AE',
    affinity: hasAffinity ? affinityByTail[tail] : 0,
    hasAffinity: hasAffinity,
    activePaperLoad: activePaperLoad,
    maxPapers: maxPapers,
    cooldownUntil: cooldownUntil,
    availability: availabilityState === 'until' ? 'Unavailable until ' + formatDate(Number(availabilityEdge && availabilityEdge.weight)) : (availabilityState === 'indefinite' ? 'Unavailable indefinitely' : 'Available'),
    availabilityLabel: availabilityState === 'until' ? 'Unavailable until ' + formatDate(Number(availabilityEdge && availabilityEdge.weight)) : (availabilityState === 'indefinite' ? 'Unavailable indefinitely' : 'Available'),
    statusSummary: [
      'Reviews ' + (row.reviewProgressData && row.reviewProgressData.numCompletedReviews || 0) + '/' + activePaperLoad,
      'Decisions ' + (row.reviewProgressData && row.reviewProgressData.numCompletedMetaReviews || 0)
    ].join('; '),
    classification: classification,
    eligible: classification.eligible,
    randomOrder: Math.random()
  };
};

var renderAutoAssignActionEditorCandidates = function(submission, candidates, assignedAe) {
  var isOssPaper = isOssSubmission(submission);
  var currentAeId = assignedAe && assignedAe.id && assignedAe.id !== 'No Action Editor' ? assignedAe.id : null;
  var assignedCandidate = currentAeId ? candidates.find(function(candidate) {
    return candidate.tail === currentAeId;
  }) : null;
  var eligibleCandidates = candidates.filter(function(candidate) {
    return !candidate.assigned && candidate.classification.severity === 'eligible';
  });
  var authorConflictCandidates = candidates.filter(function(candidate) {
    return !candidate.assigned && candidate.classification.severity === 'author_conflict';
  });
  var conflictCandidates = candidates.filter(function(candidate) {
    return !candidate.assigned && candidate.classification.severity === 'warning_conflict';
  });
  var unavailableCandidates = candidates.filter(function(candidate) {
    return !candidate.assigned && candidate.classification.severity === 'unavailable';
  });
  var blockedCandidates = candidates.filter(function(candidate) {
    return !candidate.assigned && candidate.classification.severity === 'blocked';
  });
  var displayedEligibleCandidates = eligibleCandidates.slice(0, 40);
  var displayedAuthorConflictCandidates = authorConflictCandidates.slice(0, 40);
  var displayedConflictCandidates = conflictCandidates.slice(0, 40);
  var displayedUnavailableCandidates = unavailableCandidates.slice(0, 40);
  var displayedBlockedCandidates = blockedCandidates.slice(0, 20);
  var candidatePoolLabel = isOssPaper ? 'OSS action editors' : 'regular action editors';
  var initiallySelectedTail = getSelectedActionEditorAssignmentTail() || (displayedEligibleCandidates[0] && displayedEligibleCandidates[0].tail);
  var conflictOverrideEnabled = function() {
    return ASSIGN_AE_CONFLICT_OVERRIDE_ENABLED;
  };
  var formatConflictCell = function(candidate, currentLabel) {
    if (currentLabel) return _.escape(currentLabel);
    var classification = candidate.classification || {};
    var conflictReasons = classification.conflict && classification.conflict.reasons || [];
    var conflictKind = classification.conflict && classification.conflict.kind;
    if (conflictKind === 'author_conflict' && conflictReasons.length) {
      var authorConflictLabel = classification.conflict && classification.conflict.label || 'Conflict';
      return '<strong class="text-danger">' + _.escape(authorConflictLabel) + '</strong><br>' +
        '<ul style="padding-left: 16px; margin-bottom: 0;">' +
          conflictReasons.map(function(reason) { return '<li>' + _.escape(reason.label) + '</li>'; }).join('') +
        '</ul>';
    }
    if (classification.availability && classification.availability.state !== 'available') {
      return '<span class="text-muted">' + _.escape(classification.availability.label) + '</span>';
    }
    if (classification.blockers && classification.blockers.length) {
      return classification.blockers.map(function(blocker) { return _.escape(blocker.label); }).join('; ');
    }
    if (conflictReasons.length) {
      var conflictClass = conflictKind === 'author_conflict' ? 'text-danger' : 'text-warning';
      var conflictLabel = classification.conflict && classification.conflict.label || 'Conflict';
      return '<strong class="' + conflictClass + '">' + _.escape(conflictLabel) + '</strong><br>' +
        '<ul style="padding-left: 16px; margin-bottom: 0;">' +
          conflictReasons.map(function(reason) { return '<li>' + _.escape(reason.label) + '</li>'; }).join('') +
        '</ul>';
    }
    return '<span class="text-muted">None detected</span>';
  };
  var renderCandidateTable = function(rows, options) {
    options = options || {};
    if (!rows.length) {
      return '<div class="text-muted" style="padding: 12px;">' + _.escape(options.emptyText || 'No action editors to display.') + '</div>';
    }
    return '<div class="table-responsive" style="max-height: ' + _.escape(String(options.maxHeight || 420)) + 'px; overflow-y: auto;">' +
      '<table class="table table-condensed table-striped" style="margin-bottom: 0; font-size: 12px;">' +
        '<thead>' +
          '<tr>' +
            (options.selectable ? '<th style="width: 42px;">Select</th>' : '') +
            '<th>Action Editor</th>' +
            '<th>Institution</th>' +
            '<th>Affinity</th>' +
            '<th>Load</th>' +
            '<th>Conflicts</th>' +
          '</tr>' +
        '</thead>' +
        '<tbody>' +
          rows.map(function(candidate, index) {
            var isConflictCandidate = candidate.classification && candidate.classification.severity === 'warning_conflict';
            var isAuthorConflictCandidate = candidate.classification && candidate.classification.severity === 'author_conflict';
            var disabled = !options.selectable || candidate.assigned || isAuthorConflictCandidate || (!candidate.eligible && !(isConflictCandidate && options.conflictSelectable && conflictOverrideEnabled()));
            var statusMarkup = formatConflictCell(candidate, candidate.assigned ? 'Current AE' : '');
            var affinityText = candidate.hasAffinity ? String(candidate.affinity) : '0 (missing)';
            var maxPapersText = candidate.maxPapers === Infinity ? 'unlimited' : String(candidate.maxPapers);
            var selected = !disabled && initiallySelectedTail === candidate.tail;
            var rowClass = !disabled ? 'ae-assignment-candidate-row' : '';
            if (isAuthorConflictCandidate) rowClass += ' danger';
            if (isConflictCandidate) rowClass += ' warning';
            return '<tr' + (rowClass ? ' class="' + rowClass + '" data-ae-tail="' + _.escape(candidate.tail) + '"' + (!disabled ? ' style="cursor: pointer;"' : '') : '') + '>' +
              (options.selectable ? (
                '<td><input type="radio" name="' + ACTION_EDITOR_ASSIGNMENT_RADIO_NAME + '" value="' + _.escape(candidate.tail) + '"' +
                  (selected || (!initiallySelectedTail && index === 0 && !disabled) ? ' checked' : '') +
                  (disabled ? ' disabled' : '') +
                '></td>'
              ) : '') +
              '<td><strong>' + _.escape(candidate.name) + '</strong><br><span class="text-muted">' + _.escape(candidate.tail) + '</span></td>' +
              '<td>' + (candidate.institution ? _.escape(candidate.institution) : '<span class="text-muted">None</span>') + '</td>' +
              '<td>' + _.escape(affinityText) + '</td>' +
              '<td>' + _.escape(String(candidate.activePaperLoad)) + ' / ' + _.escape(maxPapersText) + '</td>' +
              '<td>' + statusMarkup + '</td>' +
            '</tr>';
          }).join('') +
        '</tbody>' +
      '</table>' +
    '</div>';
  };

  if (currentAeId) {
    setAutoAssignAeStatus('Candidate pool: ' + candidatePoolLabel + '. This paper already has an action editor; unassign the current Action Editor before assigning another.', false);
  } else if (!eligibleCandidates.length) {
    setAutoAssignAeStatus('Candidate pool: ' + candidatePoolLabel + '. No fully eligible action editors were found. Review conflict and unavailable sections before assigning.', true);
  } else {
    setAutoAssignAeStatus('Candidate pool: ' + candidatePoolLabel + '. Showing top ' + displayedEligibleCandidates.length + ' of ' + eligibleCandidates.length + ' eligible candidates ranked by affinity; missing affinity is shown as 0. The assignment submit step still enforces eligibility, load, and cooldown.', false);
  }

  $('#confirm-auto-assign-ae-container').remove();
  $('#auto-assign-ae-status').after(
    '<div id="confirm-auto-assign-ae-container" style="max-width: 1100px; margin: 12px auto 0;">' +
      (assignedCandidate ? (
        '<div class="panel panel-default" style="text-align: left;">' +
          '<div class="panel-heading"><strong>Current assigned action editor</strong></div>' +
          renderCandidateTable([assignedCandidate], { selectable: false, maxHeight: 120 }) +
        '</div>'
      ) : '') +
      '<div class="panel panel-default" style="text-align: left;">' +
        '<div class="panel-heading"><strong>Eligible action editors</strong> <span class="text-muted">top ' + _.escape(String(displayedEligibleCandidates.length)) + ' of ' + _.escape(String(eligibleCandidates.length)) + '</span></div>' +
        renderCandidateTable(displayedEligibleCandidates, {
          selectable: true,
          emptyText: 'No eligible action editors to display.',
          maxHeight: 460
        }) +
      '</div>' +
      (displayedConflictCandidates.length ? (
        '<details class="panel panel-warning" style="text-align: left;" open>' +
          '<summary class="panel-heading" style="display: block; cursor: pointer;"><strong>OpenReview conflict warnings</strong> <span class="text-muted">showing ' + _.escape(String(displayedConflictCandidates.length)) + ' of ' + _.escape(String(conflictCandidates.length)) + '</span></summary>' +
          '<div class="panel-body" style="padding-bottom: 0;">' +
            '<div class="checkbox" style="margin-top: 0;"><label><input id="allow-ae-conflict-override" type="checkbox"' + (ASSIGN_AE_CONFLICT_OVERRIDE_ENABLED ? ' checked' : '') + '> Allow EIC override for a selected OpenReview conflict row.</label></div>' +
          '</div>' +
          renderCandidateTable(displayedConflictCandidates, { selectable: true, conflictSelectable: true, maxHeight: 320 }) +
        '</details>'
      ) : '') +
      (displayedAuthorConflictCandidates.length ? (
        '<details class="panel panel-danger" style="text-align: left;" open>' +
          '<summary class="panel-heading" style="display: block; cursor: pointer;"><strong>Author conflicts</strong> <span class="text-muted">showing ' + _.escape(String(displayedAuthorConflictCandidates.length)) + ' of ' + _.escape(String(authorConflictCandidates.length)) + '</span></summary>' +
          '<div class="panel-body" style="padding-bottom: 0;">These candidates are listed as paper authors or author-declared conflicts and cannot be selected.</div>' +
          renderCandidateTable(displayedAuthorConflictCandidates, { selectable: false, maxHeight: 260 }) +
        '</details>'
      ) : '') +
      (displayedUnavailableCandidates.length ? (
        '<details class="panel panel-default" style="text-align: left; opacity: 0.82;">' +
          '<summary class="panel-heading" style="display: block; cursor: pointer;"><strong>Unavailable action editors</strong> <span class="text-muted">showing ' + _.escape(String(displayedUnavailableCandidates.length)) + ' of ' + _.escape(String(unavailableCandidates.length)) + '</span></summary>' +
          renderCandidateTable(displayedUnavailableCandidates, { selectable: false, maxHeight: 260 }) +
        '</details>'
      ) : '') +
      (displayedBlockedCandidates.length ? (
        '<details class="panel panel-default" style="text-align: left;">' +
          '<summary class="panel-heading" style="display: block; cursor: pointer;"><strong>Other blocked action editors</strong> <span class="text-muted">showing ' + _.escape(String(displayedBlockedCandidates.length)) + ' of ' + _.escape(String(blockedCandidates.length)) + '</span></summary>' +
          renderCandidateTable(displayedBlockedCandidates, { selectable: false, maxHeight: 260 }) +
        '</details>'
      ) : '') +
      '<p class="text-center" style="margin-top: 8px;">' +
        '<button id="confirm-auto-assign-ae" type="button" class="btn btn-primary"' + (currentAeId || (!displayedEligibleCandidates.length && !(ASSIGN_AE_CONFLICT_OVERRIDE_ENABLED && displayedConflictCandidates.length)) ? ' disabled' : '') + '>Assign selected action editor</button>' +
        '<span class="action-editor-assignment-button-status text-muted" style="margin-left: 8px;"></span>' +
      '</p>' +
    '</div>'
  );

  $('#confirm-auto-assign-ae-container').off('click', '.ae-assignment-candidate-row').on('click', '.ae-assignment-candidate-row', function(event) {
    if ($(event.target).is('input')) return;
    $(this).find('input[name="' + ACTION_EDITOR_ASSIGNMENT_RADIO_NAME + '"]:not(:disabled)').prop('checked', true).trigger('change');
  });
  $('#allow-ae-conflict-override').off('change').on('change', function() {
    ASSIGN_AE_CONFLICT_OVERRIDE_ENABLED = $(this).prop('checked');
    renderAutoAssignActionEditorCandidates(submission, candidates, assignedAe);
  });

  $('#confirm-auto-assign-ae').off('click').on('click', function() {
    var selectedTail = getSelectedActionEditorAssignmentTail();
    var selectedCandidate = candidates.find(function(candidate) {
      return candidate.tail === selectedTail;
    });
    var selectedConflict = selectedCandidate && selectedCandidate.classification && selectedCandidate.classification.severity === 'warning_conflict';
    var selectedAuthorConflict = selectedCandidate && selectedCandidate.classification && selectedCandidate.classification.severity === 'author_conflict';
    if (!selectedCandidate || selectedCandidate.assigned || selectedAuthorConflict || (!selectedCandidate.eligible && !(selectedConflict && conflictOverrideEnabled()))) {
      setAutoAssignAeStatus('Select one action editor to assign.', true);
      return;
    }

    setActionEditorAssignmentButtonBusy($('#confirm-auto-assign-ae'));
    postSelectedActionEditorAssignment(
      submission,
      selectedCandidate.tail,
      $('#auto-assign-ae-status'),
      $('#confirm-auto-assign-ae'),
      'Unable to auto-assign the action editor.',
      actionEditorAssignmentOverrideLabel(selectedCandidate, conflictOverrideEnabled()),
      assignedAe
    ).then(function() {
      showActionEditorAssignmentComplete(
        $('#auto-assign-ae-status'),
        $('#confirm-auto-assign-ae'),
        'Assigned ' + selectedCandidate.name + '. Refreshing...',
        selectedCandidate.name || selectedCandidate.tail
      );
    }).fail(function(error) {
      if (!selectedConflict && assignmentConflictRejectedByBackend(error)) {
        markCandidateBackendOpenReviewConflict(submission, selectedCandidate);
        ASSIGN_AE_CONFLICT_OVERRIDE_ENABLED = true;
        setAutoAssignAeStatus('OpenReview reported a computed conflict for ' + selectedCandidate.tail + '. Review the warning row and submit with the EIC OpenReview conflict override if appropriate.', true);
        renderAutoAssignActionEditorCandidates(submission, candidates, assignedAe);
      }
    });
  });
};

var submitAutoActionEditorAssignment = function(submission, assignedAe, actionEditorRows, ossActionEditorsMaxPapers, submissionRows) {
  $('#confirm-auto-assign-ae-container').remove();
  $('#auto-assign-action-editor').prop('disabled', true).text('Checking action editors...');
  setAutoAssignAeStatus('', false);

  var matchingActionEditors = filterActionEditorRowsForSubmission(submission, actionEditorRows);
  var activeActionEditors = matchingActionEditors.filter(function(row) {
    return row.summary && row.summary.id && row.summary.status.Active === 'Active';
  });
  var isOssPaper = isOssSubmission(submission);
  var tails = _.uniq(activeActionEditors.map(function(row) {
    return row.summary.id;
  }));
  var activePaperIdsByHead = getActiveActionEditorPaperIdsByHead(actionEditorRows);
  var decisionCompletedPaperIdsByHead = getDecisionCompletedPaperIdsByHead(submissionRows);

  if (!tails.length) {
    setAutoAssignAeStatus('No active action editors were found.', true);
    $('#auto-assign-action-editor').prop('disabled', false).text('Auto-assign action editor');
    return;
  }

  $.when(
    getRecentActionEditorAssignmentEdgesByTail(submissionRows, activePaperIdsByHead, submission.id),
    Webfield2.api.getAll('/edges', { invitation: actionEditorAssignmentInvitationId(), head: submission.id }),
    Webfield2.api.getAll('/edges', { invitation: actionEditorAssignmentScoreSources().affinityScoreInvitation, head: submission.id, domain: VENUE_ID }),
    getAssignmentOpenReviewConflictEdgesByTail(submission.id, tails),
    getEdgesByTail(actionEditorAssignmentAvailabilitySources().actionEditorAvailabilityInvitation, actionEditorAssignmentAvailabilitySources().actionEditorGroup, tails),
    getEdgesByTail(actionEditorAssignmentLoadSources().customMaxPapersInvitation, actionEditorAssignmentAvailabilitySources().actionEditorGroup, tails)
  ).then(function(recentAssignmentEdgesByTail, assignmentEdges, affinityEdges, conflictsByTail, availabilityByTail, maxPapersByTail) {
    return getActionEditorAssignmentHistoryByTail(tails, recentAssignmentEdgesByTail).then(function(assignmentHistoryByTail) {
      assignmentEdges = assignmentEdges || [];
      affinityEdges = affinityEdges || [];
      var assignedTails = _.uniq(assignmentEdges.map(function(edge) { return edge.tail; }).filter(Boolean));
      var assignedTail = assignedAe && assignedAe.id && assignedAe.id !== 'No Action Editor' ? assignedAe.id : assignedTails[0];
      var affinityByTail = affinityEdges.reduce(function(byTail, edge) {
        byTail[edge.tail] = Math.max(byTail[edge.tail] === undefined ? -Infinity : byTail[edge.tail], getEdgeWeight(edge, -Infinity));
        return byTail;
      }, {});
      var rowByTail = activeActionEditors.reduce(function(byTail, row) {
        byTail[row.summary.id] = row;
        return byTail;
      }, {});
      var candidates = tails.map(function(tail) {
        var row = rowByTail[tail];
        return buildActionEditorAssignmentCandidate(submission, row, assignedAe, {
          affinityByTail: affinityByTail,
          conflictsByTail: conflictsByTail,
          availabilityByTail: availabilityByTail,
          maxPapersByTail: maxPapersByTail,
          assignmentHistoryByTail: assignmentHistoryByTail,
          activePaperIdsByHead: activePaperIdsByHead,
          decisionCompletedPaperIdsByHead: decisionCompletedPaperIdsByHead
        }, {
          ossActionEditorsMaxPapers: ossActionEditorsMaxPapers,
          assignedTail: assignedTail
        });
      }).sort(function(a, b) {
        if (a.assigned !== b.assigned) return a.assigned ? -1 : 1;
        if (b.affinity !== a.affinity) return b.affinity - a.affinity;
        return a.randomOrder - b.randomOrder;
      });

      renderAutoAssignActionEditorCandidates(submission, candidates, assignedAe);
    });
  }).fail(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to check action editors.';
    setAutoAssignAeStatus(message, true);
  }).always(function() {
    $('#auto-assign-action-editor').prop('disabled', false).text('Auto-assign action editor');
  });
};

var buildActionEditorSearchCandidates = function(submission, assignedAe, actionEditorRows, ossActionEditorsMaxPapers, affinityByTail, conflictsByTail, availabilityByTail, maxPapersByTail, assignmentHistoryByTail, submissionRows) {
  var activePaperIdsByHead = getActiveActionEditorPaperIdsByHead(actionEditorRows);
  var decisionCompletedPaperIdsByHead = getDecisionCompletedPaperIdsByHead(submissionRows);
  return filterActionEditorRowsForSubmission(submission, actionEditorRows).map(function(row) {
    return buildActionEditorAssignmentCandidate(submission, row, assignedAe, {
      affinityByTail: affinityByTail,
      conflictsByTail: conflictsByTail,
      availabilityByTail: availabilityByTail,
      maxPapersByTail: maxPapersByTail,
      assignmentHistoryByTail: assignmentHistoryByTail,
      activePaperIdsByHead: activePaperIdsByHead,
      decisionCompletedPaperIdsByHead: decisionCompletedPaperIdsByHead
    }, {
      ossActionEditorsMaxPapers: ossActionEditorsMaxPapers
    });
  });
};

var formatActionEditorSearchConflictCell = function(candidate) {
  var classification = candidate.classification || {};
  var conflictReasons = classification.conflict && classification.conflict.reasons || [];
  var conflictKind = classification.conflict && classification.conflict.kind;
  if (conflictKind === 'author_conflict' && conflictReasons.length) {
    var authorConflictLabel = classification.conflict && classification.conflict.label || 'Conflict';
    return '<strong class="text-danger">' + _.escape(authorConflictLabel) + '</strong><br>' +
      '<ul style="padding-left: 16px; margin-bottom: 0;">' +
        conflictReasons.map(function(reason) { return '<li>' + _.escape(reason.label) + '</li>'; }).join('') +
      '</ul>';
  }
  if (classification.availability && classification.availability.state !== 'available') {
    return '<span class="text-muted">' + _.escape(classification.availability.label) + '</span>';
  }
  if (classification.blockers && classification.blockers.length) {
    return classification.blockers.map(function(blocker) { return _.escape(blocker.label); }).join('; ');
  }
  if (conflictReasons.length) {
    var conflictClass = conflictKind === 'author_conflict' ? 'text-danger' : 'text-warning';
    var conflictLabel = classification.conflict && classification.conflict.label || 'Conflict';
    return '<strong class="' + conflictClass + '">' + _.escape(conflictLabel) + '</strong><br>' +
      '<ul style="padding-left: 16px; margin-bottom: 0;">' +
        conflictReasons.map(function(reason) { return '<li>' + _.escape(reason.label) + '</li>'; }).join('') +
      '</ul>';
  }
  return '<span class="text-muted">None detected</span>';
};

var renderActionEditorSearchRows = function(candidates, query, selectedTail) {
  query = (query || '').trim().toLowerCase();
  if (!query) {
    return '<p class="text-muted">Enter an action editor name, email, or OpenReview profile id.</p>';
  }
  var matches = candidates.filter(function(candidate) {
    return [candidate.name, candidate.email, candidate.institution, candidate.id].join(' ').toLowerCase().indexOf(query) >= 0;
  }).sort(function(a, b) {
    var order = { eligible: 0, author_conflict: 1, warning_conflict: 2, unavailable: 3, blocked: 4 };
    var aOrder = Object.prototype.hasOwnProperty.call(order, a.classification.severity) ? order[a.classification.severity] : 9;
    var bOrder = Object.prototype.hasOwnProperty.call(order, b.classification.severity) ? order[b.classification.severity] : 9;
    return aOrder - bOrder;
  }).slice(0, 40);
  if (!matches.length) {
    return '<p class="text-muted">No matching action editors found.</p>';
  }
  return '<div class="table-responsive" style="max-height: 360px; overflow-y: auto;">' +
    '<table class="table table-condensed table-striped" style="font-size: 12px;">' +
      '<thead><tr>' +
        '<th style="width: 42px;">Select</th>' +
        '<th>Action Editor</th>' +
        '<th>Institution</th>' +
        '<th>Affinity</th>' +
        '<th>Load</th>' +
        '<th>AE Status</th>' +
        '<th>Conflicts</th>' +
      '</tr></thead>' +
      '<tbody>' +
        matches.map(function(candidate) {
          var isConflictCandidate = candidate.classification && candidate.classification.severity === 'warning_conflict';
          var isAuthorConflictCandidate = candidate.classification && candidate.classification.severity === 'author_conflict';
          var isUnavailableCandidate = candidate.classification && candidate.classification.severity === 'unavailable';
          var conflictOverride = $('#allow-ae-search-conflict-override').prop('checked');
          var selectable = candidate.classification && candidate.classification.severity === 'eligible' || (isConflictCandidate && conflictOverride);
          var rowClass = selectable ? 'ae-assignment-candidate-row' : '';
          if (isAuthorConflictCandidate) rowClass += ' danger';
          if (isConflictCandidate) rowClass += ' warning';
          var rowStyle = selectable ? 'cursor: pointer;' : (isUnavailableCandidate ? 'color: #777; background: #f7f7f7;' : '');
          return '<tr' + (rowClass ? ' class="' + rowClass + '" data-ae-tail="' + _.escape(candidate.id) + '"' : '') + (rowStyle ? ' style="' + rowStyle + '"' : '') + '>' +
            '<td><input type="radio" name="' + ACTION_EDITOR_ASSIGNMENT_RADIO_NAME + '" value="' + _.escape(candidate.id) + '"' + (selectedTail === candidate.id ? ' checked' : '') + (selectable ? '' : ' disabled') + '></td>' +
            '<td><strong>' + _.escape(candidate.name) + '</strong><br><span class="text-muted">' + _.escape(candidate.id) + '</span></td>' +
            '<td>' + (candidate.institution ? _.escape(candidate.institution) : '<span class="text-muted">None</span>') + '</td>' +
            '<td>' + _.escape(candidate.hasAffinity ? String(candidate.affinity) : '0 (missing)') + '</td>' +
            '<td>' + _.escape(String(candidate.activePaperLoad)) + ' / ' + _.escape(String(candidate.maxPapers)) + '</td>' +
            '<td>' + _.escape(candidate.statusSummary) + '</td>' +
            '<td>' + formatActionEditorSearchConflictCell(candidate) + '</td>' +
          '</tr>';
        }).join('') +
      '</tbody>' +
    '</table>' +
  '</div>';
};

var bindActionEditorSearch = function(submission, assignedAe, actionEditorRows, ossActionEditorsMaxPapers, submissionRows) {
  var candidates = [];
  var currentAeId = getAssignedActionEditorId(assignedAe);
  var onDemandAffinityByTail = {};
  var onDemandAffinityRequests = {};
  var visibleActionEditorSearchMatches = function() {
    var query = ($('#manual-ae-search-input').val() || '').trim().toLowerCase();
    if (!query) return [];
    return candidates.filter(function(candidate) {
      return [candidate.name, candidate.email, candidate.institution, candidate.id].join(' ').toLowerCase().indexOf(query) >= 0;
    }).slice(0, 40);
  };
  var applyActionEditorConflictEdges = function(candidate, edges) {
    var conflictEdge = (edges || []).filter(function(edge) {
      return edge && !edge.ddate && (edge.weight === undefined || edge.weight === null || Number(edge.weight) !== 0);
    })[0] || null;
    candidate.classification = classifyActionEditorCandidate(submission, { summary: {
      id: candidate.id,
      name: candidate.name,
      email: candidate.email,
      allEmails: candidate.allEmails || [],
      institution: candidate.institution,
      status: { Active: candidate.active === false ? 'Not active' : 'Active' },
      profileContent: candidate.profileContent || {}
    } }, {
      id: candidate.id,
      conflictEdge: conflictEdge,
      activePaperLoad: candidate.activePaperLoad,
      maxPapers: candidate.maxPapers,
      cooldownUntil: candidate.cooldownUntil,
      assigned: candidate.assigned,
      current: candidate.assigned,
      active: candidate.active !== false
    });
    candidate.eligible = candidate.classification.eligible;
    return candidate;
  };
  var refreshSelectedActionEditorConflict = function(candidate) {
    if (!candidate || !candidate.id) return $.Deferred().resolve(candidate).promise();
    return materializeOnDemandAssignmentConflict({
      submission: submission,
      tail: candidate.id,
      signature: EDITORS_IN_CHIEF_ID
    }).then(function() {
      return getAssignmentOpenReviewConflictEdgesByTail(submission.id, [candidate.id]);
    }, function() {
      return getAssignmentOpenReviewConflictEdgesByTail(submission.id, [candidate.id]);
    }).then(function(conflictsByTail) {
      return applyActionEditorConflictEdges(candidate, conflictsByTail[candidate.id] || []);
    }, function() {
      return candidate;
    });
  };
  var requestVisibleMissingActionEditorAffinity = function() {
    visibleActionEditorSearchMatches().forEach(function(candidate) {
      if (!candidate || candidate.hasAffinity || onDemandAffinityRequests[candidate.id]) return;
      onDemandAffinityRequests[candidate.id] = true;
      requestOnDemandAssignmentAffinity({
        role: 'action-editor',
        tail: candidate.id,
        groupId: actionEditorAssignmentScoreSources().matchingInputGroup,
        invitationId: actionEditorAssignmentScoreSources().affinityScoreInvitation,
        noteId: submission.id,
        paperNumber: submission.number,
        title: submission.content && submission.content.title || '',
        abstract: submission.content && submission.content.abstract || ''
      }).then(function(result) {
        if (result && result.score !== null && result.score !== undefined) {
          onDemandAffinityByTail[result.tail] = result.score;
          candidates.forEach(function(item) {
            if (item.id === result.tail) {
              item.affinity = result.score;
              item.hasAffinity = true;
            }
          });
          updateResults();
        }
      });
    });
  };
  var updateResults = function() {
    var selectedTail = getSelectedActionEditorAssignmentTail();
    var conflictMatches = candidates.filter(function(candidate) {
      return candidate.classification && candidate.classification.severity === 'warning_conflict';
    }).length;
    var overrideChecked = $('#allow-ae-search-conflict-override').prop('checked');
    var overrideMarkup = conflictMatches
      ? '<div class="checkbox"><label><input id="allow-ae-search-conflict-override" type="checkbox"' + (overrideChecked ? ' checked' : '') + '> Allow EIC override for selected OpenReview conflict rows.</label></div>'
      : '';
    $('#manual-ae-search-results').html(overrideMarkup + renderActionEditorSearchRows(candidates, $('#manual-ae-search-input').val(), selectedTail));
    $('#assign-selected-action-editor').prop('disabled', !!currentAeId || !getSelectedActionEditorAssignmentTail());
    requestVisibleMissingActionEditorAffinity();
  };
  $('#manual-ae-search-input').off('input').on('input', updateResults);
  $('#manual-ae-search-results').off('change', 'input[name="' + ACTION_EDITOR_ASSIGNMENT_RADIO_NAME + '"]').on('change', 'input[name="' + ACTION_EDITOR_ASSIGNMENT_RADIO_NAME + '"]', updateResults);
  $('#manual-ae-search-results').off('change', '#allow-ae-search-conflict-override').on('change', '#allow-ae-search-conflict-override', updateResults);
  $('#manual-ae-search-results').off('click', '.ae-assignment-candidate-row').on('click', '.ae-assignment-candidate-row', function(event) {
    if ($(event.target).is('input')) return;
    $(this).find('input[name="' + ACTION_EDITOR_ASSIGNMENT_RADIO_NAME + '"]:not(:disabled)').prop('checked', true).trigger('change');
  });
  $('#assign-selected-action-editor').off('click').on('click', function() {
    var selectedTail = getSelectedActionEditorAssignmentTail();
    if (!selectedTail) return;
    if (currentAeId && currentAeId !== selectedTail) {
      setActionEditorAssignmentProgress($('#manual-ae-search-status'), $('#assign-selected-action-editor'), 'Unassign the current Action Editor before assigning another.', true);
      return;
    }
    var selectedCandidate = candidates.find(function(candidate) { return candidate.id === selectedTail; });
    var selectedConflict = selectedCandidate && selectedCandidate.classification && selectedCandidate.classification.severity === 'warning_conflict';
    var selectedAuthorConflict = selectedCandidate && selectedCandidate.classification && selectedCandidate.classification.severity === 'author_conflict';
    var selectedUnavailable = selectedCandidate && selectedCandidate.classification && selectedCandidate.classification.severity === 'unavailable';
    if (selectedAuthorConflict) {
      $('#manual-ae-search-status').removeClass('text-muted').addClass('text-danger').text('This action editor is blocked by an author conflict.');
      return;
    }
    if (!selectedCandidate || selectedUnavailable || (!selectedCandidate.eligible && !(selectedConflict && $('#allow-ae-search-conflict-override').prop('checked')))) {
      $('#manual-ae-search-status').removeClass('text-muted').addClass('text-danger').text('This action editor is not currently eligible for assignment.');
      return;
    }
    setActionEditorAssignmentButtonBusy($('#assign-selected-action-editor'));
    setActionEditorAssignmentProgress($('#manual-ae-search-status'), $('#assign-selected-action-editor'), 'Refreshing conflict status for ' + selectedTail + '...', false);
    refreshSelectedActionEditorConflict(selectedCandidate).then(function(refreshedCandidate) {
      selectedConflict = refreshedCandidate && refreshedCandidate.classification && refreshedCandidate.classification.severity === 'warning_conflict';
      selectedAuthorConflict = refreshedCandidate && refreshedCandidate.classification && refreshedCandidate.classification.severity === 'author_conflict';
      selectedUnavailable = refreshedCandidate && refreshedCandidate.classification && refreshedCandidate.classification.severity === 'unavailable';
      if (selectedAuthorConflict) {
        setActionEditorAssignmentProgress($('#manual-ae-search-status'), $('#assign-selected-action-editor'), 'This action editor is blocked by an author conflict.', true);
        restoreActionEditorAssignmentButton($('#assign-selected-action-editor'));
        updateResults();
        return;
      }
      if (selectedUnavailable || (!refreshedCandidate.eligible && !(selectedConflict && $('#allow-ae-search-conflict-override').prop('checked')))) {
        setActionEditorAssignmentProgress($('#manual-ae-search-status'), $('#assign-selected-action-editor'), 'This action editor is not currently eligible for assignment.', true);
        restoreActionEditorAssignmentButton($('#assign-selected-action-editor'));
        updateResults();
        return;
      }
      setActionEditorAssignmentProgress($('#manual-ae-search-status'), $('#assign-selected-action-editor'), 'Submitting action editor assignment...', false);
      postSelectedActionEditorAssignment(
        submission,
        selectedTail,
        $('#manual-ae-search-status'),
        $('#assign-selected-action-editor'),
        'Unable to assign the selected action editor.',
        actionEditorAssignmentOverrideLabel(refreshedCandidate, $('#allow-ae-search-conflict-override').prop('checked')),
        assignedAe
      ).then(function() {
        showActionEditorAssignmentComplete(
          $('#manual-ae-search-status'),
          $('#assign-selected-action-editor'),
          'Assigned selected action editor. Refreshing...',
          refreshedCandidate.name || refreshedCandidate.tail
        );
      }).fail(function(error) {
        if (!selectedConflict && assignmentConflictRejectedByBackend(error)) {
          markCandidateBackendOpenReviewConflict(submission, selectedCandidate);
          setActionEditorAssignmentProgress($('#manual-ae-search-status'), $('#assign-selected-action-editor'), 'OpenReview reported a computed conflict for ' + selectedTail + '. Review the warning row and check the EIC OpenReview conflict override before resubmitting.', true);
          restoreActionEditorAssignmentButton($('#assign-selected-action-editor'));
          updateResults();
        }
      });
    });
  });
  var activeRows = filterActionEditorRowsForSubmission(submission, actionEditorRows).filter(function(row) {
    return row.summary && row.summary.id;
  });
  var tails = _.uniq(activeRows.map(function(row) {
    return row.summary.id;
  }));
  if (!tails.length) {
    candidates = [];
    updateResults();
    return;
  }
  $('#manual-ae-search-results').html('<p class="text-muted">Loading current action editor availability...</p>');
  var activePaperIdsByHead = getActiveActionEditorPaperIdsByHead(actionEditorRows);
  $.when(
    getRecentActionEditorAssignmentEdgesByTail(submissionRows, activePaperIdsByHead, submission.id),
    Webfield2.api.getAll('/edges', { invitation: actionEditorAssignmentScoreSources().affinityScoreInvitation, head: submission.id, domain: VENUE_ID }),
    getAssignmentOpenReviewConflictEdgesByTail(submission.id, tails),
    getEdgesByTail(actionEditorAssignmentAvailabilitySources().actionEditorAvailabilityInvitation, actionEditorAssignmentAvailabilitySources().actionEditorGroup, tails),
    getEdgesByTail(actionEditorAssignmentLoadSources().customMaxPapersInvitation, actionEditorAssignmentAvailabilitySources().actionEditorGroup, tails)
  ).then(function(recentAssignmentEdgesByTail, affinityEdges, conflictsByTail, availabilityByTail, maxPapersByTail) {
    return getActionEditorAssignmentHistoryByTail(tails, recentAssignmentEdgesByTail).then(function(assignmentHistoryByTail) {
      var affinityByTail = (affinityEdges || []).reduce(function(byTail, edge) {
        byTail[edge.tail] = Math.max(byTail[edge.tail] === undefined ? -Infinity : byTail[edge.tail], getEdgeWeight(edge, -Infinity));
        return byTail;
      }, onDemandAffinityByTail);
      candidates = buildActionEditorSearchCandidates(submission, assignedAe, actionEditorRows, ossActionEditorsMaxPapers, affinityByTail, conflictsByTail, availabilityByTail, maxPapersByTail, assignmentHistoryByTail, submissionRows);
      updateResults();
    });
  }).fail(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to load current action editor availability.';
    candidates = [];
    $('#manual-ae-search-status').removeClass('text-muted').addClass('text-danger').text(message);
    updateResults();
  });
};

var renderAssignActionEditorTab = function(venueStatusData) {
  var requestedMode = getAssignActionEditorRequestedMode();
  var selectedPaperId = typeof ASSIGN_AE_PAPER_ID !== 'undefined' ? ASSIGN_AE_PAPER_ID : args && args.assignAePaper;
  var row = selectedPaperId && venueStatusData.submissionStatusRows.find(function(candidate) {
    return candidate.submission.id === selectedPaperId || candidate.submission.forum === selectedPaperId;
  });

  if (!row) {
    $('#notes').html(
      '<div class="container">' +
        '<p class="text-muted">This assignment invitation could not find the selected paper context.</p>' +
      '</div>'
    );
    return;
  }

  var submission = row.submission;
  if (typeof JMLRPermissionHelpers !== 'undefined' && JMLRPermissionHelpers.loadActorContext && JMLRPermissionHelpers.loadPaperContext && JMLRPermissionHelpers.loadVenueContext && JMLRPermissionHelpers.getRoleContextAccessModel) {
    var actorContext = JMLRPermissionHelpers.loadActorContext(user || {}).model.actor_context;
    var eicGroupCache = {};
    eicGroupCache[EDITORS_IN_CHIEF_ID] = venueStatusData.roleContextGroups && venueStatusData.roleContextGroups.editorsInChief;
    var paperContext = JMLRPermissionHelpers.loadPaperContext({
      submission: submission,
      groups: eicGroupCache
    }).model.paper_context;
    var venueContext = JMLRPermissionHelpers.loadVenueContext({
      venue_id: VENUE_ID,
      role_groups: {
        eic: EDITORS_IN_CHIEF_ID
      }
    }).model.venue_context;
    var selectedPaperRoleAccess = JMLRPermissionHelpers.getRoleContextAccessModel(actorContext, paperContext, {
      entry_point: 'assign_action_editor',
      requested_role_context: getAssignActionEditorRoleContext(),
      required_role_context: 'eic',
      venue_context: venueContext
    });
    if (!selectedPaperRoleAccess.ok) {
      $('#notes').html(
        '<div class="container">' +
          '<div class="alert alert-danger" role="alert">This paper cannot be opened in the editor-in-chief assignment context for the current user.</div>' +
        '</div>'
      );
      return;
    }
  }
  var title = _.escape(submission.content.title || ('Paper ' + submission.number));
  var abstract = _.escape(submission.content.abstract || '');
  var coverLetter = _.escape((submission.content.cover_letter || '').trim());
  var coverLetterBody = coverLetter
    ? '<p style="margin-top: 8px; white-space: pre-wrap;">' + coverLetter + '</p>'
    : '<p class="text-muted" style="margin-top: 8px;">No cover letter was provided.</p>';
  var paperReferrerUrl = encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + '#paper-status)');
  var paperUrl = appendRoleContext('/forum?id=' + encodeURIComponent(submission.id) + '&referrer=' + paperReferrerUrl, resolveConsolePaperRoleContext(submission, 'eic', EDITORS_IN_CHIEF_ID));
  var pdfUrl = '/pdf?id=' + encodeURIComponent(submission.id);
  var assignedAe = row.actionEditorProgressData && row.actionEditorProgressData.actionEditor;
  var actionEditorAssignmentEdge = row.actionEditorProgressData && row.actionEditorProgressData.actionEditorAssignmentEdge;
  var currentAeModel = JMLRPermissionHelpers.getSelectedPaperActionEditorModel(row, actionEditorAssignmentEdge, Date.now()).model;
  var assignedAeText = currentAeModel.current_action_editor && currentAeModel.current_action_editor.id && currentAeModel.current_action_editor.id !== 'No Action Editor'
    ? _.escape(currentAeModel.current_action_editor.name || currentAeModel.current_action_editor.id)
    : 'None';
  var currentAeId = getAssignedActionEditorId(assignedAe);
  var currentAeRemovalControls = currentAeId
    ? '<div id="current-action-editor-removal-controls">' +
      '<hr style="margin: 12px 0;">' +
      '<div class="checkbox" style="margin-bottom: 8px;"><label><input id="remove-current-action-editor-checkbox" type="checkbox" value="' + _.escape(currentAeId) + '"> Remove current Action Editor</label></div>' +
      '<button id="remove-current-action-editor" type="button" class="btn btn-xs btn-danger">Remove selected action editor</button>' +
      '<span class="action-editor-assignment-button-status text-muted" style="margin-left: 8px;"></span>' +
      '</div>'
    : '<p class="text-muted" style="margin-bottom: 0;">No current Action Editor is assigned.</p>';
  var currentAePanel =
    '<section class="panel panel-default">' +
      '<div class="panel-heading"><strong>Current action editor</strong></div>' +
      '<div class="panel-body">' +
        '<p><strong>Action Editor:</strong> <span id="current-action-editor-name">' + assignedAeText + '</span></p>' +
        '<p><strong>Assignment date:</strong> <span id="current-action-editor-assignment-date">' + (currentAeModel.assignment_time ? _.escape(formatDate(currentAeModel.assignment_time)) : 'Unknown') + '</span></p>' +
        '<p><strong>Assigned duration:</strong> ' + (currentAeModel.assigned_days === null ? 'Unknown' : _.escape(String(currentAeModel.assigned_days)) + ' days') + '</p>' +
        '<p><strong>Review progress:</strong> ' + _.escape(String(currentAeModel.submitted_reviews)) + ' submitted / ' + _.escape(String(currentAeModel.assigned_reviewers)) + ' assigned; release threshold ' + _.escape(String(currentAeModel.required_reviewers)) + '</p>' +
        '<p><strong>Pending reviews:</strong> ' + _.escape(String(currentAeModel.pending_reviews)) + '</p>' +
        '<p><strong>Decision status:</strong> ' + _.escape(String(currentAeModel.decision_status || 'No decision')) + '</p>' +
        currentAeRemovalControls +
      '</div>' +
    '</section>';

  $('#notes').html(
    '<div class="container">' +
      '<style>' +
        '.jmlr-assignment-collapsible { margin-bottom: 12px; }' +
        '.jmlr-assignment-collapsible > summary { cursor: pointer; list-style: none; border-radius: 4px; padding: 4px 6px; }' +
        '.jmlr-assignment-collapsible > summary::-webkit-details-marker { display: none; }' +
        '.jmlr-assignment-collapsible > summary:hover { background: #f5f5f5; }' +
        '.jmlr-assignment-collapsible > summary:focus-visible { outline: 2px solid #337ab7; outline-offset: 2px; }' +
        '.jmlr-assignment-caret { display: inline-block; margin-right: 6px; transition: transform 0.15s ease-in-out; }' +
        '.jmlr-assignment-collapsible:not([open]) .jmlr-assignment-caret { transform: rotate(-90deg); }' +
      '</style>' +
      '<p class="dark">Use this page to assign an action editor for <a href="' + paperUrl + '">Paper ' + submission.number + ': ' + title + '</a> ' +
        '(<a href="' + pdfUrl + '" target="_blank" rel="noopener noreferrer">PDF</a>).</p>' +
      currentAePanel +
      '<details class="dark jmlr-assignment-collapsible" open>' +
        '<summary><span class="jmlr-assignment-caret" aria-hidden="true">&#9662;</span><strong>Abstract</strong></summary>' +
        '<p style="margin-top: 8px; white-space: pre-wrap;">' + abstract + '</p>' +
      '</details>' +
      '<details class="dark jmlr-assignment-collapsible" open>' +
        '<summary><span class="jmlr-assignment-caret" aria-hidden="true">&#9662;</span><strong>Cover Letter</strong></summary>' +
        coverLetterBody +
      '</details>' +
      '<p class="text-center" style="margin-top: 16px;">' +
        '<button id="show-previous-action-editor" type="button" class="btn btn-lg btn-default" style="margin-right: 8px; display: none; font-size: 18px;" disabled>Previous AE</button>' +
        '<button id="auto-assign-action-editor" type="button" class="btn btn-lg btn-default" style="margin-right: 8px; font-size: 18px;" disabled>Auto-assign action editor</button>' +
        '<button id="show-search-action-editor" type="button" class="btn btn-lg btn-default" style="font-size: 18px;" disabled>Search action editors</button>' +
      '</p>' +
      '<p id="auto-assign-ae-status" class="text-center text-muted" style="margin-top: 12px;">Loading author profile conflict checks...</p>' +
      '<p id="previous-ae-assignment-status" class="text-center text-muted"></p>' +
      '<section id="previous-ae-assignment-section" style="display: none; margin-top: 16px;"></section>' +
      '<section id="manual-ae-search-section" class="panel panel-default" style="display: none; margin-top: 16px;">' +
        '<div class="panel-heading"><strong>Search action editors</strong></div>' +
        '<div class="panel-body">' +
          '<p class="text-muted">Search existing JMLR action editors by name, email, or OpenReview profile id. Final assignment is still checked by the backend assignment process.</p>' +
          '<input id="manual-ae-search-input" type="search" class="form-control" placeholder="Search action editors" style="max-width: 420px; margin-bottom: 10px;">' +
          '<div id="manual-ae-search-results"></div>' +
          '<p style="margin-top: 10px;">' +
            '<button id="assign-selected-action-editor" type="button" class="btn btn-primary" disabled>Assign selected action editor</button>' +
            '<span class="action-editor-assignment-button-status text-muted" style="margin-left: 8px;"></span>' +
          '</p>' +
          '<p id="manual-ae-search-status" class="text-muted"></p>' +
        '</div>' +
      '</section>' +
    '</div>'
  );
  $('#remove-current-action-editor').off('click').on('click', function() {
    var removeButton = $(this);
    var removeStatus = $('#remove-current-action-editor-status');
    if (!$('#remove-current-action-editor-checkbox').prop('checked')) {
      setActionEditorAssignmentProgress(removeStatus, removeButton, 'Check Remove current Action Editor before submitting.', true);
      return;
    }
    setActionEditorAssignmentButtonBusy(removeButton);
    setActionEditorAssignmentProgress(removeStatus, removeButton, 'Removing current Action Editor...', false);
    postCurrentActionEditorRemoval(submission, assignedAe, actionEditorAssignmentEdge, removeStatus, removeButton);
  });

  loadSubmissionAuthorProfiles(submission).then(function(authorProfiles) {
    submission.authorProfiles = authorProfiles || [];
    submission.browserConflictModel = getSubmissionBrowserConflictModel(submission);
    $('#auto-assign-action-editor').prop('disabled', false);
    $('#show-search-action-editor').prop('disabled', false);
    setAutoAssignAeStatus('', false);
    renderPreviousActionEditorAssignment(submission, assignedAe, venueStatusData.actionEditorStatusRows);

    $('#auto-assign-action-editor').off('click').on('click', function() {
      $('#manual-ae-search-section').hide();
      $('#previous-ae-assignment-section').hide();
      submitAutoActionEditorAssignment(submission, assignedAe, venueStatusData.actionEditorStatusRows, venueStatusData.ossActionEditorsMaxPapers, venueStatusData.submissionStatusRows);
    });
    $('#show-search-action-editor').off('click').on('click', function() {
      $('#confirm-auto-assign-ae-container').remove();
      $('#previous-ae-assignment-section').hide();
      setAutoAssignAeStatus('', false);
      $('#manual-ae-search-section').show();
      $('#manual-ae-search-input').trigger('focus');
      var searchPanel = $('#manual-ae-search-section')[0];
      if (searchPanel && searchPanel.scrollIntoView) searchPanel.scrollIntoView({ block: 'start' });
    });
    bindActionEditorSearch(submission, assignedAe, venueStatusData.actionEditorStatusRows, venueStatusData.ossActionEditorsMaxPapers, venueStatusData.submissionStatusRows);

    if (requestedMode === 'auto') {
      setTimeout(function() {
        $('#auto-assign-action-editor').trigger('click');
      }, 0);
    } else if (requestedMode === 'search') {
      setTimeout(function() {
        $('#show-search-action-editor').trigger('click');
      }, 0);
    } else if (requestedMode === 'previous') {
      setTimeout(function() {
        $('#show-previous-action-editor').trigger('click');
      }, 0);
    }
  });
};

var getAssignActionEditorRequestedMode = function() {
  if (typeof args !== 'undefined' && args && (args.mode === 'auto' || args.mode === 'search' || args.mode === 'previous')) return args.mode;

  var urls = [];
  if (typeof location !== 'undefined') urls.push(location.href);
  if (typeof performance !== 'undefined' && performance.getEntriesByType) {
    var navigationEntries = performance.getEntriesByType('navigation') || [];
    navigationEntries.forEach(function(entry) {
      if (entry && entry.name) urls.push(entry.name);
    });
  }
  if (typeof document !== 'undefined' && document && document.referrer) urls.push(document.referrer);

  for (var i = 0; i < urls.length; i += 1) {
    try {
      var baseUrl = typeof location !== 'undefined' && location.origin ? location.origin : null;
      var url = baseUrl ? new URL(urls[i], baseUrl) : new URL(urls[i]);
      var hashParams = new URLSearchParams(String(url.hash || '').replace(/^#/, ''));
      var mode = url.searchParams.get('mode') || hashParams.get('mode');
      if (mode === 'auto' || mode === 'search' || mode === 'previous') return mode;
    } catch (error) {
      // Ignore malformed referrer/navigation values.
    }
  }
  return '';
};

var renderAssignActionEditorInvitation = function(venueStatusData) {
  renderAssignActionEditorTab(venueStatusData);
};
