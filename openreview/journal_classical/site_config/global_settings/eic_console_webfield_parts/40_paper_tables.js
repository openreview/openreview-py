var prepareAssignmentPagesAndRefresh = function(link, submission) {
  if (link.data('jmlrAssignmentSetupInFlight')) return;
  link.data('jmlrAssignmentSetupInFlight', true);
  var container = link.closest('.eic-assignment-setup-control');
  var status = container.find('.eic-assignment-setup-status');
  status.removeClass('text-danger').addClass('text-muted').text('Creating paper-specific assignment pages...');
  link.addClass('disabled').attr('aria-disabled', 'true');
  setupAssignmentPagesForPaper(submission, function(attempt) {
    status
      .removeClass('text-danger')
      .addClass('text-muted')
      .text('Still creating assignment pages for Paper ' + submission.number + '... ' + (attempt * 2) + 's elapsed.');
  }).then(function() {
    link.removeClass('btn-primary').addClass('btn-success');
    status.removeClass('text-danger').addClass('text-muted').text('Assignment pages are ready. Refresh the page to see assignment controls.');
  }).fail(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to prepare assignment pages.';
    status.removeClass('text-muted').addClass('text-danger').text(message);
    link.removeClass('disabled').removeAttr('aria-disabled');
    link.data('jmlrAssignmentSetupInFlight', false);
  });
};

var setPreviousContinuityStatus = function(link, message, isError) {
  var container = link.closest('.eic-previous-continuity-control');
  var status = container.find('.eic-previous-continuity-status');
  status
    .removeClass('text-danger text-muted')
    .addClass(isError ? 'text-danger' : 'text-muted')
    .text(message || '');
};

var postPreviousContinuityAssignmentRequest = function(submission) {
  return Webfield2.api.post('/notes/edits?awaitProcess=true', {
    invitation: VENUE_ID + '/-/Previous_Continuity_Assignment',
    signatures: [EDITORS_IN_CHIEF_ID],
    note: {
      signatures: [EDITORS_IN_CHIEF_ID],
      content: {
        note_id: { value: submission.id },
        paper_number: { value: submission.number },
        trigger_source: { value: 'eic_console' }
      }
    }
  });
};

var previousContinuityActionEditorAlreadyAssigned = function(submission, previousAeId) {
  return Webfield2.api.getAll('/edges', {
    invitation: VENUE_ID + '/Paper' + submission.number + '/Action_Editors/-/Assignment',
    head: submission.id,
    domain: VENUE_ID
  }).then(function(edges) {
    return (edges || []).some(function(edge) {
      return edge && !edge.ddate && edge.tail === previousAeId;
    });
  }, function() {
    return false;
  });
};

var reviewerAnonIdFromSelectedDecisionField = function(fieldName) {
  if (!fieldName || fieldName === 'reviewers') return '';
  return String(fieldName).replace('resubmission_auto_assign_reviewer_', '').replace('reviewer_', '');
};

var loadSelectedPreviousReviewerProfiles = function(previousSubmission, selectedReviewerFields) {
  var anonIds = _.uniq((selectedReviewerFields || []).map(reviewerAnonIdFromSelectedDecisionField).filter(Boolean));
  var chain = anonIds.reduce(function(promise, anonId) {
    return promise.then(function(profiles) {
      return Webfield2.api.get('/groups', {
        id: VENUE_ID + '/Paper' + previousSubmission.number + '/Reviewer_' + anonId,
        limit: 1,
        select: 'members'
      }).then(function(result) {
        var group = result && result.groups && result.groups[0] || {};
        (group.members || []).forEach(function(member) {
          if (member && member.charAt(0) === '~' && profiles.indexOf(member) < 0) profiles.push(member);
        });
        return profiles;
      }, function() {
        return profiles;
      });
    });
  }, $.Deferred().resolve([]).promise());
  return chain;
};

var waitForPreviousContinuityAssignmentReadback = function(submission, previousAeId, selectedReviewerProfiles, attempt) {
  var currentAttempt = attempt || 0;
  var aeAssignmentId = VENUE_ID + '/Paper' + submission.number + '/Action_Editors/-/Assignment';
  var reviewerAssignmentId = VENUE_ID + '/Paper' + submission.number + '/Reviewers/-/Assignment';
  var reviewerGroupId = VENUE_ID + '/Paper' + submission.number + '/Reviewers';
  var selectedProfiles = selectedReviewerProfiles || [];
  return $.when(
    Webfield2.api.getAll('/edges', {
      invitation: aeAssignmentId,
      head: submission.id,
      domain: VENUE_ID
    }),
    Webfield2.api.getAll('/edges', {
      invitation: reviewerAssignmentId,
      head: submission.id,
      domain: VENUE_ID
    }),
    Webfield2.api.get('/groups', {
      id: reviewerGroupId,
      limit: 1,
      select: 'members'
    })
  ).then(function(aeEdges, reviewerEdges, reviewerGroupResult) {
    var activeAeEdges = (aeEdges || []).filter(function(edge) {
      return edge && !edge.ddate;
    });
    var activeReviewerEdges = (reviewerEdges || []).filter(function(edge) {
      return edge && !edge.ddate;
    });
    var activeReviewerTails = activeReviewerEdges.map(function(edge) { return edge.tail; }).filter(Boolean);
    var previousAeAssigned = activeAeEdges.some(function(edge) {
      return edge.tail === previousAeId;
    });
    var missingReviewerProfiles = selectedProfiles.filter(function(profileId) {
      return activeReviewerTails.indexOf(profileId) < 0;
    });
    if (previousAeAssigned) {
      return {
        previousAeAssigned: true,
        activeAeTails: activeAeEdges.map(function(edge) { return edge.tail; }),
        activeReviewerTails: activeReviewerTails,
        selectedReviewerProfiles: selectedProfiles,
        missingReviewerProfiles: missingReviewerProfiles,
        reviewerGroupMembers: (reviewerGroupResult && reviewerGroupResult.groups && reviewerGroupResult.groups[0] || {}).members || []
      };
    }
    if (currentAttempt >= 60) {
      return $.Deferred().reject({
        message: 'Previous AE assignment did not appear in assignment edges within the bounded wait.',
        previousAeAssigned: previousAeAssigned,
        activeAeTails: activeAeEdges.map(function(edge) { return edge.tail; }),
        activeReviewerTails: activeReviewerTails,
        selectedReviewerProfiles: selectedProfiles,
        missingReviewerProfiles: missingReviewerProfiles,
        reviewerGroupMembers: (reviewerGroupResult && reviewerGroupResult.groups && reviewerGroupResult.groups[0] || {}).members || []
      }).promise();
    }
    return waitForMilliseconds(2000).then(function() {
      return waitForPreviousContinuityAssignmentReadback(submission, previousAeId, selectedProfiles, currentAttempt + 1);
    });
  });
};

var loadPreviousContinuityCurrentState = function(submission, previousAeId, selectedReviewerProfiles) {
  var aeAssignmentId = VENUE_ID + '/Paper' + submission.number + '/Action_Editors/-/Assignment';
  var reviewerAssignmentId = VENUE_ID + '/Paper' + submission.number + '/Reviewers/-/Assignment';
  var reviewerGroupId = VENUE_ID + '/Paper' + submission.number + '/Reviewers';
  return $.when(
    Webfield2.api.getAll('/edges', {
      invitation: aeAssignmentId,
      head: submission.id,
      domain: VENUE_ID
    }),
    Webfield2.api.getAll('/edges', {
      invitation: reviewerAssignmentId,
      head: submission.id,
      domain: VENUE_ID
    }),
    Webfield2.api.get('/groups', {
      id: reviewerGroupId,
      limit: 1,
      select: 'members'
    })
  ).then(function(aeEdges, reviewerEdges, reviewerGroupResult) {
    var activeReviewerTails = (reviewerEdges || []).filter(function(edge) {
      return edge && !edge.ddate && edge.tail;
    }).map(function(edge) { return edge.tail; });
    var selectedProfiles = selectedReviewerProfiles || [];
    var missingReviewerProfiles = selectedProfiles.filter(function(profileId) {
      return activeReviewerTails.indexOf(profileId) < 0;
    });
    return {
      previousAeAssigned: (aeEdges || []).some(function(edge) {
        return edge && !edge.ddate && edge.tail === previousAeId;
      }),
      selectedReviewerProfiles: selectedProfiles,
      missingReviewerProfiles: missingReviewerProfiles,
      reviewerGroupMembers: (reviewerGroupResult && reviewerGroupResult.groups && reviewerGroupResult.groups[0] || {}).members || [],
      activeReviewerTails: activeReviewerTails
    };
  }, function() {
    return {
      previousAeAssigned: false,
      selectedReviewerProfiles: selectedReviewerProfiles || [],
      missingReviewerProfiles: selectedReviewerProfiles || [],
      reviewerGroupMembers: [],
      activeReviewerTails: []
    };
  });
};

var autoAssignPreviousContinuityAndRefresh = function(link, submission) {
  if (link.data('jmlrPreviousContinuityInFlight')) return;
  link.data('jmlrPreviousContinuityInFlight', true);
  setPreviousContinuityStatus(link, 'Resolving previous submission and selected reviewers...', false);
  link.addClass('disabled').attr('aria-disabled', 'true');
  resolvePreviousSubmissionForAssignment(submission).then(function(previousSubmission) {
    if (!previousSubmission) {
      return $.Deferred().reject({ message: 'No previous JMLR submission could be resolved for this resubmission.' }).promise();
    }
    setPreviousContinuityStatus(link, 'Checking previous AE and reviewer continuity choices...', false);
    return $.when(
      loadPreviousActionEditorAssignment(previousSubmission),
      loadSelectedPreviousReviewerProfilesForContinuity(previousSubmission)
    ).then(function(previousAssignment, selectedReviewerProfiles) {
      if (!previousAssignment || !previousAssignment.tail) {
        return $.Deferred().reject({ message: 'No previous action editor assignment was found for the previous submission.' }).promise();
      }
      return $.Deferred().resolve(selectedReviewerProfiles || []).then(function(selectedReviewerProfiles) {
        var hasSelectedReviewers = selectedReviewerProfiles.length > 0;
        setPreviousContinuityStatus(link, 'Submitting checked assignment request...', false);
        return previousContinuityActionEditorAlreadyAssigned(submission, previousAssignment.tail).then(function(previousAeAlreadyAssigned) {
          if (previousAeAlreadyAssigned) {
            setPreviousContinuityStatus(link, 'Previous AE is already assigned. Confirming readback...', false);
            return waitForPreviousContinuityAssignmentReadback(submission, previousAssignment.tail, selectedReviewerProfiles, 0);
          }
          return postPreviousContinuityAssignmentRequest(submission).then(function() {
            setPreviousContinuityStatus(link, hasSelectedReviewers
              ? 'Assignment submitted. Confirming AE readback; selected reviewers are best-effort.'
              : 'Assignment submitted. Confirming AE readback...', false);
            return waitForPreviousContinuityAssignmentReadback(submission, previousAssignment.tail, selectedReviewerProfiles, 0);
          });
        });
      });
    });
  }).then(function(readback) {
    link.removeClass('btn-default').addClass('btn-success');
    setPreviousContinuityStatus(link, readback && readback.missingReviewerProfiles && readback.missingReviewerProfiles.length
      ? 'Previous AE assigned. Selected previous reviewers were not all assigned automatically; finish reviewer assignment manually if needed. Refresh the page to see current assignment state.'
      : 'Assignment complete. Refresh the page to see current assignment state.', false);
  }).fail(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to auto-assign previous continuity.';
    setPreviousContinuityStatus(link, message, true);
    link.removeClass('disabled').removeAttr('aria-disabled');
    link.data('jmlrPreviousContinuityInFlight', false);
  });
};

var previousContinuityButtonHtml = function(previousContinuity) {
  if (!previousContinuity || !previousContinuity.hasPreviousSubmissionReference) return '';
  return '<div class="mt-2 eic-previous-continuity-control">' +
    '<button type="button" class="btn btn-default btn-xs eic-auto-assign-previous-continuity" disabled data-note-id="' + _.escape(previousContinuity.noteId) + '" data-paper-number="' + _.escape(String(previousContinuity.paperNumber)) + '" data-previous-url="' + _.escape(previousContinuity.previousUrl || '') + '" data-previous-number="' + _.escape(String(previousContinuity.previousNumber || '')) + '" data-previous-list="' + _.escape(String(previousContinuity.previousList || '')) + '">Checking previous AE/reviewers...</button>' +
    '<span class="small text-muted eic-previous-continuity-status" style="margin-left: 8px;">Checking previous AE/reviewer continuity...</span>' +
  '</div>';
};

var replacePreviousContinuityControl = function(link, html) {
  var control = link.closest('.eic-previous-continuity-control');
  if (control.length) {
    control.replaceWith(html);
  } else {
    link.replaceWith(html);
  }
};

var previousContinuityFromTableRow = function(data, row) {
  var previousContinuity = data && (data.previousContinuity || (data.actionEditorProgressData && data.actionEditorProgressData.previousContinuity));
  if (previousContinuity) return previousContinuity;
  var sourceRow = row || data || {};
  var submission = sourceRow.submission;
  if (!submission || !hasPreviousSubmissionReference(submission)) return null;
  return {
    hasPreviousSubmissionReference: true,
    hasAssignmentSurfaces: sourceRow.assignmentSetupData && sourceRow.assignmentSetupData.hasAssignmentSurfaces,
    noteId: submission.id,
    paperNumber: submission.number,
    previousUrl: getContentValue(submission.content, 'previous_JMLR_submission_URL') || submission.previousSubmissionUrl || '',
    previousNumber: getContentValue(submission.content, 'previous_JMLR_submission_number') || '',
    previousList: getContentValue(submission.content, 'previous_JMLR_submissions') || ''
  };
};

var renderActionEditorDecisionCell = function(data, row) {
  var previousContinuity = previousContinuityFromTableRow(data, row);
  var actionEditor = data && data.actionEditor || data && data.areachair || {};
  var actionEditorName = actionEditor.name || actionEditor.id || 'No Action Editor';
  var actionEditorId = actionEditor.id && actionEditor.id !== actionEditorName
    ? ' <span class="text-muted">' + _.escape(actionEditor.id) + '</span>'
    : '';
  return '<p class="mb-1"><strong>Action Editor:</strong> ' +
    _.escape(actionEditorName) + actionEditorId + '</p>' +
    previousContinuityButtonHtml(previousContinuity);
};

var renderEicReviewerStatusCell = function(data) {
  var reviewers = Object.values(data && data.reviewers || {});
  var submittedCount = data && data.numSubmittedReviews || 0;
  var assignedCount = data && data.numReviewers || reviewers.length || 0;
  var html = '<p class="mb-1"><strong>' + _.escape(String(submittedCount)) + ' of ' +
    _.escape(String(assignedCount)) + ' reviews submitted</strong></p>';
  if (!reviewers.length) {
    return html + '<p class="text-muted small mb-0">No reviewers assigned.</p>';
  }
  html += '<ul class="list-unstyled mb-0">';
  reviewers.forEach(function(reviewer) {
    var reviewerName = reviewer.name || reviewer.id || reviewer.anonymousGroupId || 'Reviewer';
    var reviewerId = reviewer.id && reviewer.id !== reviewerName
      ? ' <span class="text-muted">' + _.escape(reviewer.id) + '</span>'
      : '';
    html += '<li class="mb-1"><span>' + _.escape(reviewerName) + reviewerId + '</span>' +
      ' <span class="label ' + (reviewer.completedReview ? 'label-success' : 'label-default') + '">' +
      (reviewer.completedReview ? 'Submitted' : 'Not submitted') + '</span></li>';
  });
  html += '</ul>';
  return html;
};

var refreshPreviousContinuityControls = function(container) {
  $(container + ' .eic-auto-assign-previous-continuity').each(function() {
    var $link = $(this);
    var submission = {
      id: $link.attr('data-note-id'),
      number: parseInt($link.attr('data-paper-number'), 10),
      content: {
        previous_JMLR_submission_URL: $link.attr('data-previous-url') || '',
        previous_JMLR_submission_number: $link.attr('data-previous-number') || '',
        previous_JMLR_submissions: $link.attr('data-previous-list') || ''
      },
      previousSubmissionUrl: $link.attr('data-previous-url') || ''
    };
    resolvePreviousSubmissionForAssignment(submission).then(function(previousSubmission) {
      if (!previousSubmission) {
        replacePreviousContinuityControl($link, '<span class="text-muted small eic-previous-continuity-unavailable">Previous AE/reviewer continuity unavailable.</span>');
        return;
      }
      return $.when(
        loadPreviousActionEditorAssignment(previousSubmission),
        loadSelectedPreviousReviewerProfilesForContinuity(previousSubmission)
      ).then(function(previousAssignment, selectedReviewerProfiles) {
        if (!previousAssignment || !previousAssignment.tail) {
          replacePreviousContinuityControl($link, '<span class="text-muted small eic-previous-continuity-unavailable">Previous AE/reviewer continuity unavailable.</span>');
          return;
        }
        return $.Deferred().resolve(selectedReviewerProfiles || []).then(function(selectedReviewerProfiles) {
          return loadPreviousContinuityCurrentState(submission, previousAssignment.tail, selectedReviewerProfiles).then(function(currentState) {
            if (currentState.previousAeAssigned) {
              replacePreviousContinuityControl($link, '<span class="text-muted small eic-previous-continuity-complete">' +
                (currentState.missingReviewerProfiles.length
                  ? 'Previous AE continuity complete. Finish selected previous reviewers manually if needed.'
                  : (selectedReviewerProfiles.length ? 'Previous AE/reviewer continuity complete.' : 'Previous AE continuity complete.')) +
                '</span>');
              return;
            }
            $link.text(selectedReviewerProfiles.length ? 'Auto-assign previous AE/reviewers' : 'Auto-assign previous AE').prop('disabled', false);
            setPreviousContinuityStatus($link, selectedReviewerProfiles.length
              ? 'Previous AE and selected previous reviewers are available for continuity assignment.'
              : 'Previous AE is available for continuity assignment. No previous reviewers were selected on the prior decision.', false);
          });
        });
      });
    });
  });
};

var bindPreviousContinuityControls = function(container) {
  $(container + ' .eic-auto-assign-previous-continuity').off('click.jmlrPreviousContinuity').on('click.jmlrPreviousContinuity', function(event) {
    event.preventDefault();
    var $link = $(this);
    var submission = {
      id: $link.attr('data-note-id'),
      number: parseInt($link.attr('data-paper-number'), 10),
      content: {
        previous_JMLR_submission_URL: $link.attr('data-previous-url') || '',
        previous_JMLR_submission_number: $link.attr('data-previous-number') || '',
        previous_JMLR_submissions: $link.attr('data-previous-list') || ''
      },
      previousSubmissionUrl: $link.attr('data-previous-url') || ''
    };
    autoAssignPreviousContinuityAndRefresh($link, submission);
  });
  refreshPreviousContinuityControls(container);
};

var renderEicNoteSummary = function(data) {
  var html = Handlebars.templates.noteSummary(data);
  if (!data || !data.paperUrl) return html;
  return html.replace(/href="\/forum\?id=[^"]+"/, 'href="' + _.escape(data.paperUrl) + '"');
};

var renderTable = function(container, rows) {
  var tableRows = rows.map(function(row) {
    return {
      checked: row.checked,
      submissionNumber: row.submissionNumber,
      submission: row.submission,
      actionEditorProgressData: row.actionEditorProgressData,
      reviewProgressData: row.reviewProgressData,
      status: row.status
    };
  });
  Webfield2.ui.renderTable('#' + container, tableRows, {
    headings: [
      '<input type="checkbox" class="select-all-papers">',
      '#',
      'Paper Summary',
      'AE',
      'Reviewers',
      'Status'
    ],
    renders: [
      function(data) {
        return '<label><input type="checkbox" class="select-note-reviewers" data-note-id="' +
          data.noteId + '" ' + (data.checked ? 'checked="checked"' : '') + '></label>';
      },
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      function(data) {
        return renderEicNoteSummary(data) + renderPreviousSubmissionLink(data) + previousContinuityButtonHtml(data && data.previousContinuity) + renderJmlrSubmissionDetails(data);
      },
      renderActionEditorDecisionCell,
      renderEicReviewerStatusCell,
      function(data) {
        var status = data;
        while (status && typeof status === 'object' && status.value !== undefined) {
          status = status.value;
        }
        return '<h4>' + _.escape(String(status || '')) + '</h4>';
      }
    ],
    sortOptions: {
      Paper_Number: function(row) { return row.submissionNumber.number; },
      Paper_Title: function(row) { return _.toLower(_.trim(row.submission.content.title)); },
      Paper_Submission_Date: function(row) { return row.submission.cdate; },
      Number_of_Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
      Number_of_Reviews_Missing: function(row) { return (row.reviewProgressData.requiredReviewers || row.reviewProgressData.numReviewers) - row.reviewProgressData.numSubmittedReviews; },
      Decision: function(row) { return row.actionEditorProgressData.recommendation; },
      Status: function(row) { return row.status; },
      Review_Due_Date: function(row) { return row.reviewProgressData.duedate; },
      Earliest_Late_Due_Date: function(row) { return row.actionEditorProgressData.earlylateTaskDueDate; }
    },
    searchProperties: {
      number: ['submissionNumber.number'],
      id: ['submission.id'],
      title: ['submission.content.title'],
      submissionDate: ['submission.cdate'],
      author: ['submission.content.authors', 'note.content.authorids'], // multi props
      keywords: ['submission.content.keywords'],
      reviewer: ['reviewProgressData.reviewerSearchData'],
      numReviewersAssigned: ['reviewProgressData.numReviewers'],
      numReviewsDone: ['reviewProgressData.numSubmittedReviews'],
      decision: ['actionEditorProgressData.recommendation'],
      status: ['status'],
      default: ['submissionNumber.number', 'submission.content.title'],
      certifications: ['submission.content.certifications'],
    },
    reminderOptions: {
      container: 'a.send-reminder-link',
      defaultSubject: SHORT_PHRASE + ' Reminder',
      defaultBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the submission page:\n\n{{forumUrl}}\n\n' +
        'Thank you,\n' + SHORT_PHRASE + ' Editor-in-Chief',
      replyTo: EDITORS_IN_CHIEF_EMAIL,
      messageInvitationId: VENUE_ID + '/-/Edit',
      messageSignature: VENUE_ID,
      menu: [{
        id: 'all-reviewers',
        name: 'All reviewers of selected papers',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return rows.map(function(row) {
            return {
              groups: selectedIds.includes(row.submission.id)
                ? Object.values(row.reviewProgressData.reviewers)
                : [],
              forumUrl: '/forum?' + $.param({
                id: row.submission.forum
              })
            }
          });
        },
        messageBody: 'This is the message body'
      },
      {
        id: 'all-action-editors',
        name: 'All action editors of selected papers',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return rows.map(function(row) {
            return {
              groups: selectedIds.includes(row.submission.id)
                ? [row.actionEditorProgressData.actionEditor]
                : [],
              forumUrl: '/forum?' + $.param({
                id: row.submission.forum
              })
            }
          });
        },
        messageBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your decision for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the submission page:\n\n{{forumUrl}}\n\n' +
        'Thank you,\n' + SHORT_PHRASE + ' Editor-in-Chief'
      },
      {
        id: 'all-authors',
        name: 'All authors of selected papers',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return rows.map(function(row) {
            return {
              groups: selectedIds.includes(row.submission.id)
                ? row.submission.content.authorids.map(function(authorId) { return { id: authorId, name: view.prettyId(authorId), email: authorId };})
                : [],
              forumUrl: '/forum?' + $.param({
                id: row.submission.forum
              })
            }
          });
        },
        messageBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your camera ready revision for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the submission page:\n\n{{forumUrl}}\n\n' +
        'Thank you,\n' + SHORT_PHRASE + ' Editor-in-Chief',
      },
      {
        id: 'unsubmitted-reviews',
        name: 'Reviewers with missing reviews',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return rows.map(function(row) {
            return {
              groups: selectedIds.includes(row.submission.id)
                ? Object.values(row.reviewProgressData.reviewers).filter(function(r) {
                    return row.submission.content.venueid === UNDER_REVIEW_STATUS && !r.completedReview;
                  })
                : [],
              forumUrl: '/forum?' + $.param({
                id: row.submission.forum,
                noteId: row.submission.forum,
                invitationId: Webfield2.utils.getInvitationId(VENUE_ID, row.submission.number, REVIEW_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME })
              })
            }
          });
        }
      }]
    },
    extraClasses: 'console-table paper-table',
    pageSize: 10,
    postRenderTable: function() {
      $('#' + container + ' .console-table th').eq(0).css('width', '2%');  // [ ]
      $('#' + container + ' .console-table th').eq(1).css('width', '4%');  // #
      $('#' + container + ' .console-table th').eq(2).css('width', '33%'); // Paper Summary
      $('#' + container + ' .console-table th').eq(3).css('width', '18%'); // AE
      $('#' + container + ' .console-table th').eq(4).css('width', '28%'); // Reviewers
      $('#' + container + ' .console-table th').eq(5).css('width', '15%'); // Status
      bindPreviousContinuityControls('#' + container);
    },
    preferredEmailsInvitationId: PREFERRED_EMAILS_ID
  });
};

var renderPendingTasksList = function(container, rows) {
  var html = '<div class="container">';
  html += '<ul class="list-unstyled submissions-list task-list eic-task-list mt-0 mb-0">';
  if (!rows.length) {
    html += '<li class="note"><p class="empty-message mb-0">No pending EIC tasks.</p></li>';
  }
  rows.forEach(function(row) {
    var title = _.escape(row.submission.content.title || ('Paper ' + row.submission.number));
    var setupReady = row.assignmentSetupData && row.assignmentSetupData.hasSetupReadiness && row.assignmentSetupData.hasAssignmentSurfaces;
    var setupStateStatus = row.assignmentSetupData && row.assignmentSetupData.setupStateStatus || 'needed';
    var previousReference = hasPreviousSubmissionReference(row.submission);
    html += '<li class="note">';
    if (setupReady) {
      html += '<p class="mb-1"><strong><a href="' + _.escape(row.submission.paperUrl) + '">Paper ' + row.submission.number + ': ' + title + '</a></strong></p>';
      html += '<p class="text-muted small mb-1">Assignment pages are ready. Use checked assignment actions for this paper.</p>';
      html += '<p class="mb-0">';
      if (previousReference) {
        html += previousContinuityButtonHtml(row.actionEditorProgressData && row.actionEditorProgressData.previousContinuity);
        html += '</p><p class="text-muted small mb-0">Manual fallback: open the paper forum link and use its paper-scoped Assign Action Editor launcher.</p>';
      } else {
        html += '<a class="btn btn-primary btn-xs" href="' + _.escape(getActionEditorAssignmentPageUrl(row.submission)) + '">Assign Action Editor</a>';
        html += '</p>';
      }
    } else if (setupStateStatus === 'in_progress') {
      html += '<p class="mb-1"><strong>Paper ' + row.submission.number + ': ' + title + '</strong></p>';
      html += '<p class="text-muted small mb-1">Assignment page setup is in progress. Assignment controls appear after setup completes.</p>';
      html += '<p class="mb-0"><button type="button" class="btn btn-default btn-xs" disabled>Setup in progress</button></p>';
    } else {
      html += '<p class="mb-1"><strong>Paper ' + row.submission.number + ': ' + title + '</strong></p>';
      html += '<p class="text-muted small mb-1">Create assignment pages computes assignment setup data and creates the paper-scoped Action Editor and reviewer assignment pages. Assignment controls appear after setup completes.</p>';
      html += '<div class="mb-0 eic-assignment-setup-control"><button type="button" class="btn btn-primary btn-xs eic-create-assignment-pages" data-note-id="' + _.escape(row.submission.id) + '" data-paper-number="' + _.escape(String(row.submission.number)) + '">' + (setupStateStatus === 'stale_in_progress' || setupStateStatus === 'failed' ? 'Retry setup' : 'Create assignment pages') + '</button><span class="small text-muted eic-assignment-setup-status" style="margin-left: 8px;"></span></div>';
    }
    html += '</li>';
  });
  html += '</ul>';
  html += '</div>';
  $(container).html(html);
  $(container + ' .eic-create-assignment-pages').on('click', function(event) {
    event.preventDefault();
    var $link = $(this);
    var submission = {
      id: $link.attr('data-note-id'),
      number: parseInt($link.attr('data-paper-number'), 10)
    };
    prepareAssignmentPagesAndRefresh($link, submission);
  });
  bindPreviousContinuityControls(container);
};
