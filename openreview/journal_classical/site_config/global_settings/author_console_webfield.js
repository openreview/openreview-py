// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Author Console Webfield
// ------------------------------------

// Constants

var VENUE_ID = 'JMLR';
var SHORT_PHRASE = {{VENUE_SHORT_NAME_JSON}};
var WEBSITE = 'jmlr.org';
var SUBMISSION_ID = 'JMLR/-/Submission';
var REVIEWERS_ID = VENUE_ID + '/Reviewers';
var REVIEWER_VOLUNTEER_ID = VENUE_ID + '/-/Reviewer_Volunteer';
var SUBMISSION_GROUP_NAME = 'Paper';
var CONSOLE_FETCH_LIMIT = 100000;

var HEADER = {
  title: SHORT_PHRASE + ' Author Console',
  instructions: 'Visit the <a href="https://' + WEBSITE + '" target="_blank" rel="nofollow"> ' + SHORT_PHRASE + ' website</a> for the author guidelines.'
};
var AUTHOR_NAME = 'Authors';
var ACTION_EDITORS_NAME = 'Action_Editors';
var REVIEW_NAME = 'Review';
var DECISION_NAME = 'Decision';
var CAMERA_READY_REVISION_NAME = 'Camera_Ready_Revision';
var AE_RECOMMENDATION_ID = VENUE_ID + '/' + ACTION_EDITORS_NAME + '/-/Recommendation';
var ASSIGNED_AE_STATUS = VENUE_ID + '/Assigned_AE';
var UNDER_REVIEW_STATUS = VENUE_ID + '/Under_Review';
var DECISION_PENDING_STATUS = VENUE_ID + '/Decision_Pending';
var CAMERA_READY_REVISION_PENDING_STATUS = VENUE_ID + '/Camera_Ready_Revision_Pending';
var CAMERA_READY_CHECK_PENDING_STATUS = VENUE_ID + '/Camera_Ready_Check_Pending';
var CAMERA_READY_APPROVED_STATUS = VENUE_ID + '/Camera_Ready_Approved';
var CAMERA_READY_PUBLISHED_STATUS = VENUE_ID + '/Camera_Ready_Published';
var PUBLICATION_RETRACTED_STATUS = VENUE_ID + '/Publication_Retracted';

var getSignedInAuthorListLine = function(profile) {
  profile = profile || (user && user.profile);
  if (!profile || !profile.id || !user || _.startsWith(user.id, 'guest_')) {
    return null;
  }

  return profile.id;
};

var signedInProfile = null;
var authoredSubmissionUrlByNumber = {};

var getContentValue = function(content, fieldName) {
  var field = content && content[fieldName];
  return field && field.value !== undefined ? field.value : field;
};

var getLocationOrigin = function() {
  if (typeof globalThis !== 'undefined' && globalThis.location && globalThis.location.origin) {
    return globalThis.location.origin;
  }
  if (typeof location !== 'undefined' && location.origin) {
    return location.origin;
  }
  return '';
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
    requested_role_context: roleContext
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
  var venueContext = helpers.loadVenueContext({ venue_id: VENUE_ID }).model.venue_context;
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

var shouldShowPreviousSubmissionField = function(fieldName, value) {
  return fieldName !== 'previous_JMLR_submission_number' && fieldName !== 'previous_JMLR_submission_URL';
};

var renderJmlrSubmissionDetails = function(submission, options) {
  options = options || {};
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

  var openAttribute = options.open ? ' open' : '';
  return '<div class="jmlr-submission-metadata" style="margin-top: 8px; font-size: 13px; line-height: 1.4;">' +
    '<details' + openAttribute + '>' +
      '<summary><strong>Submission Metadata</strong></summary>' +
      '<div style="margin-top: 8px;">' +
        '<p style="margin-bottom: 6px;"><strong>Main Paper PDF:</strong> <a href="' + pdfUrl + '" target="_blank" rel="noopener noreferrer">Open PDF</a></p>' +
        (isNonEmptyAttachment(supplementaryValue) ? '<p style="margin-bottom: 6px;"><strong>Supplementary Material:</strong> <a href="/attachment?id=' + encodeURIComponent(paperId) + '&name=supplementary_material" target="_blank" rel="noopener noreferrer">Open supplementary material</a></p>' : '') +
        (isNonEmptyAttachment(replyToReviewersValue) ? '<p style="margin-bottom: 6px;"><strong>Response to Reviewers:</strong> <a href="/attachment?id=' + encodeURIComponent(paperId) + '&name=response_to_reviewers" target="_blank" rel="noopener noreferrer">Open response to reviewers</a></p>' : '') +
        '<p style="margin-bottom: 6px;"><strong>Open Source Software:</strong> ' + (isOss ? 'Yes' : 'No') + '</p>' +
        (previousSubmissionsHtml ? '<div style="margin-bottom: 6px;"><strong>Previous JMLR Submissions:</strong>' + previousSubmissionsHtml + '</div>' : '') +
        '<details style="margin-top: 6px;"><summary><strong>Cover Letter</strong></summary><pre style="white-space: pre-wrap; margin: 6px 0 0; background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; padding: 8px;">' + _.escape(coverLetter || 'No cover letter was provided.') + '</pre></details>' +
        '<details style="margin-top: 6px;"><summary><strong>Author List</strong></summary><pre style="white-space: pre-wrap; margin: 6px 0 0; background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; padding: 8px;">' + _.escape(authorList || 'No author list was provided.') + '</pre></details>' +
      '</div>' +
    '</details>' +
  '</div>';
};

var deriveAuthorPaperStatus = function(submission, decision) {
  var venueid = submission.content.venueid && submission.content.venueid.value;
  if (typeof JMLRPermissionHelpers !== 'undefined' && JMLRPermissionHelpers.getPublicationLifecycleLabel) {
    var publicationLabel = JMLRPermissionHelpers.getPublicationLifecycleLabel(venueid, VENUE_ID);
    if (publicationLabel) return publicationLabel;
  }
  if (venueid === CAMERA_READY_PUBLISHED_STATUS) return 'Published';
  if (venueid === PUBLICATION_RETRACTED_STATUS) return 'Publication retracted';
  if (venueid === CAMERA_READY_APPROVED_STATUS) return 'Camera ready approved';
  if (venueid === CAMERA_READY_CHECK_PENDING_STATUS) return 'Camera-ready check pending';
  if (venueid === CAMERA_READY_REVISION_PENDING_STATUS) return 'Camera-ready revision requested';
  if (decision && decision.content && decision.content.recommendation && decision.content.recommendation.value) {
    return decision.content.recommendation.value;
  }
  if (decision ||
      venueid === DECISION_PENDING_STATUS ||
      venueid === VENUE_ID ||
      (venueid && venueid.indexOf('/Rejected') >= 0)) {
    return 'Decision made';
  }
  if (venueid === UNDER_REVIEW_STATUS) {
    return 'Reviewer assigned';
  }
  if (venueid === ASSIGNED_AE_STATUS) {
    return 'AE assigned';
  }
  return 'Submitted';
};

var ensureApi2ApiUrl = function() {
  var api2Url = typeof OR_API_V2_URL !== 'undefined' && OR_API_V2_URL ? OR_API_V2_URL : null;
  if (!api2Url) {
    return;
  }

  OR_API_URL = api2Url;
  if (typeof globalThis !== 'undefined' && globalThis) {
    globalThis.OR_API_URL = api2Url;
    if (globalThis.window) {
      globalThis.window.OR_API_URL = api2Url;
    }
  }
  if (typeof window !== 'undefined' && window) {
    window.OR_API_URL = api2Url;
  }
};

var ensureApi2FileChunkUpload = function() {
  ensureApi2ApiUrl();

  if (typeof Webfield2 === 'undefined' || Webfield2.jmlrApi2FileChunkUploadPatched) {
    return;
  }

  Webfield2.sendFileChunk = function(formData, progressElement) {
    var apiUrl = typeof OR_API_URL !== 'undefined' && OR_API_URL ? OR_API_URL : '';
    if (!apiUrl && typeof location !== 'undefined' && location.origin) {
      apiUrl = location.origin.replace('://', '://api2.');
    }
    if (!apiUrl) {
      return $.Deferred().reject(new Error('Unable to determine the OpenReview API URL for file upload.')).promise();
    }
    var progress = progressElement && progressElement.find ? progressElement : (progressElement ? $(progressElement) : $());
    return $.ajax({
      url: apiUrl + '/attachment/chunk',
      type: 'put',
      contentType: false,
      processData: false,
      data: formData,
      headers: {
        'Access-Control-Allow-Origin': '*'
      },
      xhrFields: {
        withCredentials: true
      },
      success: function(response) {
        if (response && !response.url && progress.length) {
          var values = Object.values(response);
          if (values.length) {
            var percent = ((100 * values.filter(function(value) { return value === 'completed'; }).length) / values.length).toFixed(0) + '%';
            progress.find('.progress-bar').css('width', percent).text(percent);
          }
        }
      }
    });
  };
  Webfield2.jmlrApi2FileChunkUploadPatched = true;
};

var ensureSubmissionEditSignaturePost = function() {
  if (typeof Webfield2 === 'undefined' || !Webfield2.post || Webfield2.jmlrSubmissionSignaturePostPatched) {
    return;
  }

  var originalPost = Webfield2.post;
  Webfield2.post = function(url, payload, options) {
    var profileId = user && user.profile && user.profile.id;
    if (url === '/notes/edits' &&
        payload &&
        payload.invitation === SUBMISSION_ID) {
      url = '/notes/edits?awaitProcess=true';
      if ((!payload.signatures || !payload.signatures.length) &&
          profileId &&
          _.startsWith(profileId, '~')) {
        payload.signatures = [profileId];
      }
    }
    return originalPost.call(this, url, payload, options);
  };
  Webfield2.jmlrSubmissionSignaturePostPatched = true;
};

var ensureSubmissionEditorAlignment = function(editor) {
  if (!$('#jmlr-submission-editor-alignment').length) {
    $('head').append(
      '<style id="jmlr-submission-editor-alignment">' +
      '#new-submission .note_editor, #new-submission .note_editor * { text-align: left !important; }' +
      '</style>'
    );
  }
  if (editor && editor.length) {
    editor.css('text-align', 'left');
  }
};

var relabelMainPaperPdf = function(editor) {
  if (!editor || !editor.length) {
    return;
  }
  var pdfInput = editor.find('input[name="pdf"], input.note_pdf').first();
  var heading = pdfInput.closest('.row').find('.small_heading').first();
  if (!heading.length) {
    return;
  }
  var requiredMarker = heading.find('.required_field').first().prop('outerHTML') || '';
  heading.html(requiredMarker + 'Main Paper PDF');
};

var getGroupMembers = function(group) {
  if (group && Array.isArray(group.members)) {
    return group.members;
  }
  if (group && group.group && Array.isArray(group.group.members)) {
    return group.group.members;
  }
  if (group && Array.isArray(group.groups) && group.groups.length) {
    return group.groups[0].members || [];
  }
  return [];
};

var renderReviewerVolunteerButton = function() {
  if (!user || _.startsWith(user.id, 'guest_')) return $.Deferred().resolve().promise();
  var profileId = user && user.profile && user.profile.id;
  if (!profileId || !_.startsWith(profileId, '~')) return $.Deferred().resolve().promise();
  if ($('#author-console-reviewer-volunteer').length) return $.Deferred().resolve().promise();

  return Webfield2.api.getGroup(REVIEWERS_ID, { select: 'id,members' }).then(function(group) {
    var members = getGroupMembers(group);
    if (members.indexOf(profileId) >= 0) {
      return;
    }
    return Webfield2.get('/invitations', { id: REVIEWER_VOLUNTEER_ID }).then(function(result) {
      var invitation = result.invitations && result.invitations[0];
      if (!invitation) return;
      var container = $(
        '<div id="author-console-reviewer-volunteer" class="text-right" style="margin: 0 0 1rem;"></div>'
      );
      $('#group-container').append(container);
      var invitationForEditor = $.extend(true, {}, invitation);
      if (invitationForEditor.edit) {
        invitationForEditor.edit.signatures = [profileId];
      }
      var button = view.mkInvitationButton(invitationForEditor, function() {
        if ($('.note_editor', container).length) {
          $('.note_editor', container).slideUp('normal', function() {
            $(this).remove();
          });
          return;
        }
        view2.mkNewNoteEditor(invitationForEditor, null, null, user, {
          onCompleted: function(editor) {
            if (!editor) return;
            editor.hide();
            container.append(editor);
            editor.slideDown();
          },
          onValidate: function(invitationObj, formData) {
            if (formData.confirmation !== 'Yes, I am willing to review for JMLR' &&
                (!_.isArray(formData.confirmation) || formData.confirmation.indexOf('Yes, I am willing to review for JMLR') < 0)) {
              return ['Please confirm that you are willing to review for JMLR.'];
            }
            formData.confirmation = 'Yes, I am willing to review for JMLR';
            formData.signatures = [profileId];
            formData.editSignatureInputValues = [profileId];
            return [];
          },
          onNoteCreated: function() {
            container.removeClass('text-right').html(
              '<div class="alert alert-success text-left" role="alert" style="margin-top: 0.5rem;">' +
                '<strong>Thank you.</strong> You have been added to the JMLR reviewer pool. You can adjust your reviewing load from the Reviewer Console.' +
              '</div>'
            );
          }
        });
      });
      container.append(button);
      container.find('button, a.btn').first().text('Willing to review for JMLR');
    });
  }, function() {
    return;
  });
};

var updateSubmittingAuthorListGuidance = function(container, profile) {
  var authorListLine = getSignedInAuthorListLine(profile);
  if (!container || !container.length) {
    return;
  }

  container.find('.submission-author-list-helper').remove();
  if (!authorListLine) {
    return;
  }

  var authorListInput = container.find('textarea[name="author_list"], input[name="author_list"]').first();
  if (!authorListInput.length) {
    return;
  }

  var profileHint = container.find('.jmlr-author-list-profile-id-hint');
  if (!profileHint.length) {
    profileHint = $('<p class="jmlr-author-list-profile-id-hint text-muted" style="margin: 4px 0 8px;"></p>');
    authorListInput.before(profileHint);
  }
  profileHint.text('For example, your OpenReview profile ID is ' + authorListLine + '.');
};

var parseAuthorNamesFromList = function(authorList) {
  return (authorList || '').split(',').map(function(part) {
    return part.trim();
  }).filter(Boolean);
};

var parseAuthorListForSubmission = function(authorList) {
  if (String(authorList || '').match(/[\r\n]/)) {
    return {
      error: 'Author List must use comma-separated OpenReview profile IDs only. Line breaks are not allowed.'
    };
  }
  var authorids = [];
  (authorList || '').split(',').forEach(function(part) {
    var authorid = part.trim();
    if (authorid) {
      authorids.push(authorid);
    }
  });

  if (!authorids.length) {
    return {
      error: 'Author List is required. Enter every author by OpenReview profile ID, in paper order, for example: ~First_Author1, ~Second_Author1.'
    };
  }

  var seen = {};
  for (var i = 0; i < authorids.length; i += 1) {
    var authorid = authorids[i];
    var entryNumber = i + 1;
    if (!/^~[A-Za-z0-9_]+[0-9]*$/.test(authorid)) {
      return {
        error: 'Author List entry ' + entryNumber + ' must be a valid OpenReview profile ID like ~First_Author1. Email addresses and names are not allowed: ' + authorid + '.'
      };
    }
    if (seen[authorid]) {
      return { error: 'Author List contains a duplicate OpenReview profile ID: ' + authorid + '.' };
    }
    seen[authorid] = true;
  }

  return {
    authors: authorids,
    authorids: authorids,
    authorList: authorids.join(', ')
  };
};

var validateSubmittingAuthorForSubmission = function(authorids) {
  var profileId = user && user.profile && user.profile.id;
  if (!profileId || !_.startsWith(profileId, '~')) {
    return 'You must be signed in with an OpenReview profile to submit.';
  }
  if (authorids.indexOf(profileId) < 0) {
    return 'The submitting author must be included in Author List using their OpenReview profile ID: ' + profileId + '.';
  }
  return null;
};

var authorNamesFromNote = function(note) {
  var content = (note && note.content) || {};
  var authors = content.authors && (content.authors.value || content.authors);
  if (_.isArray(authors) && authors.length) {
    return authors;
  }
  var authorList = content.author_list && (content.author_list.value || content.author_list);
  var names = parseAuthorNamesFromList(authorList);
  if (names.length) {
    return names;
  }
  return _.isArray(authors) ? authors : [];
};

var normalizeAuthorNameForChangeCheck = function(name) {
  var normalized = String(name || '').trim().toLowerCase().replace(/\s+/g, ' ');
  if (!normalized) {
    return '';
  }
  if (normalized.indexOf(',') >= 0) {
    var pieces = normalized.split(',');
    var lastParts = (pieces[0] || '').trim().split(/\s+/).filter(Boolean);
    var restParts = (pieces.slice(1).join(',') || '').trim().split(/\s+/).filter(Boolean);
    if (lastParts.length && restParts.length) {
      return restParts[0] + ' ' + lastParts[0];
    }
  }
  var parts = normalized.replace(/,/g, ' ').split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return parts[0] + ' ' + parts[parts.length - 1];
  }
  return parts[0] || '';
};

var authorNameCounts = function(names) {
  return names.reduce(function(result, name) {
    var normalizedName = normalizeAuthorNameForChangeCheck(name);
    if (normalizedName) {
      result[normalizedName] = (result[normalizedName] || 0) + 1;
    }
    return result;
  }, {});
};

var authorNameCountDiff = function(previousNames, currentNames) {
  var previousCounts = authorNameCounts(previousNames);
  var currentCounts = authorNameCounts(currentNames);
  var keys = _.uniq(Object.keys(previousCounts).concat(Object.keys(currentCounts))).sort();
  var added = [];
  var removed = [];
  keys.forEach(function(key) {
    var previousCount = previousCounts[key] || 0;
    var currentCount = currentCounts[key] || 0;
    if (currentCount > previousCount) {
      _.times(currentCount - previousCount, function() { added.push(key); });
    } else if (previousCount > currentCount) {
      _.times(previousCount - currentCount, function() { removed.push(key); });
    }
  });
  return {
    added: added,
    removed: removed,
    matches: added.length === 0 && removed.length === 0
  };
};

var renderAuthorChangePanel = function(editor, state) {
  var previousNumberInput = editor.find('input[name="previous_JMLR_submission_number"]').first();
  if (!previousNumberInput.length) {
    return;
  }
  var panel = editor.find('.author-change-confirmation-panel');
  if (!panel.length) {
    panel = $('<div class="author-change-confirmation-panel well well-sm" style="margin: 8px 0 14px; text-align: left; font-size: 13px; line-height: 1.4;"></div>');
    var insertionTarget = previousNumberInput.closest('.row, .form-group, .note_content_field');
    if (insertionTarget.length) {
      insertionTarget.after(panel);
    } else {
      previousNumberInput.after(panel);
    }
  }
  editor.data('authorChangeState', state || null);
  panel.empty();

  if (!state || state.status === 'empty') {
    panel.hide();
    return;
  }
  if (state.status === 'loading') {
    panel.show().append('<p class="text-muted" style="margin: 0;">Checking previous submission author names...</p>');
    return;
  }
  if (state.status === 'error') {
    panel.show().append('<p class="text-danger" style="margin: 0;">' + _.escape(state.message) + '</p>');
    return;
  }
  if (state.status === 'match') {
    panel.show().append('<p class="text-success" style="margin: 0;">Author names match the previous JMLR submission after ignoring order and middle names.</p>');
    return;
  }

  var previousList = state.previousNames.length ? state.previousNames : ['None'];
  var currentList = state.currentNames.length ? state.currentNames : ['None'];
  var added = state.added.length ? state.added : ['None'];
  var removed = state.removed.length ? state.removed : ['None'];
  panel.show().append(
    '<div style="font-weight: 600; margin-bottom: 6px;">Resubmission author policy for previous JMLR submission ' + _.escape(state.previousNumber) + '.</div>' +
    '<p class="text-muted" style="margin-bottom: 8px;">Only author ordering changes are allowed for resubmissions. Adding, removing, replacing, renaming, or otherwise changing authors is not allowed. Impermissible author changes may cause desk rejection or later rejection at editorial discretion. This warning does not block submission.</p>' +
    '<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 8px;">' +
      '<div><div style="font-weight: 600;">Previous authors</div><pre style="white-space: pre-wrap; margin: 4px 0 0;">' + _.escape(previousList.join('\n')) + '</pre></div>' +
      '<div><div style="font-weight: 600;">Current authors</div><pre style="white-space: pre-wrap; margin: 4px 0 0;">' + _.escape(currentList.join('\n')) + '</pre></div>' +
    '</div>' +
    '<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 8px;">' +
      '<div><div style="font-weight: 600;">Added</div><pre style="white-space: pre-wrap; margin: 4px 0 0;">' + _.escape(added.join('\n')) + '</pre></div>' +
      '<div><div style="font-weight: 600;">Removed</div><pre style="white-space: pre-wrap; margin: 4px 0 0;">' + _.escape(removed.join('\n')) + '</pre></div>' +
    '</div>'
  );
};

var setupAuthorChangeDetection = function(editor) {
  var authorListInput = editor.find('textarea[name="author_list"], input[name="author_list"]').first();
  var previousNumberInput = editor.find('input[name="previous_JMLR_submission_number"]').first();
  if (!authorListInput.length || !previousNumberInput.length) {
    return;
  }

  var lastRequestKey = null;
  var update = _.debounce(function() {
    var previousNumber = (previousNumberInput.val() || '').trim();
    var currentNames = parseAuthorNamesFromList(authorListInput.val());
    if (!previousNumber || previousNumber.toUpperCase() === 'N/A') {
      renderAuthorChangePanel(editor, { status: 'empty' });
      return;
    }
    if (!/^\d+$/.test(previousNumber)) {
      renderAuthorChangePanel(editor, { status: 'error', message: 'Previous JMLR Submission Number must be a number, or N/A for a new submission.' });
      return;
    }
    var requestKey = previousNumber + '|' + currentNames.join('|');
    lastRequestKey = requestKey;
    renderAuthorChangePanel(editor, { status: 'loading' });
    Webfield2.api.get('/notes', { invitation: SUBMISSION_ID, number: Number(previousNumber), domain: VENUE_ID })
    .then(function(result) {
      if (lastRequestKey !== requestKey) {
        return;
      }
      var previousNote = result && result.notes && result.notes[0];
      if (!previousNote) {
        renderAuthorChangePanel(editor, { status: 'error', message: 'Could not find previous JMLR submission number ' + previousNumber + '.' });
        return;
      }
      var previousNames = authorNamesFromNote(previousNote);
      var previousUrl = '/forum?id=' + previousNote.id;
      var diff = authorNameCountDiff(previousNames, currentNames);
      if (diff.matches) {
        renderAuthorChangePanel(editor, {
          status: 'match',
          previousNumber: previousNumber,
          previousUrl: previousUrl,
          previousNames: previousNames,
          currentNames: currentNames
        });
        return;
      }
      renderAuthorChangePanel(editor, {
        status: 'mismatch',
        previousNumber: previousNumber,
        previousUrl: previousUrl,
        previousNames: previousNames,
        currentNames: currentNames,
        added: diff.added,
        removed: diff.removed,
        summary: 'Added: ' + (diff.added.join(', ') || 'None') + '; Removed: ' + (diff.removed.join(', ') || 'None')
      });
    })
    .fail(function() {
      if (lastRequestKey === requestKey) {
        renderAuthorChangePanel(editor, { status: 'error', message: 'Could not check author names for previous JMLR submission number ' + previousNumber + '.' });
      }
    });
  }, 500);

  authorListInput.on('input change', update);
  previousNumberInput.on('input change', update);
  update();
};

function main() {

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Pending Tasks', 'Your Submissions'],
    referrer: args && args.referrer
  });
  JMLRPermissionHelpers.renderVenueHomepageStrip({ container: '#group-container', venueId: VENUE_ID, $: $ });
  renderReviewerVolunteerButton();

  var loadDelay = args && args.submissionPending ? 5000 : 0;
  setTimeout(function() {
    loadData()
    .then(formatData)
    .then(renderData)
    .then(Webfield2.ui.done)
    .fail(Webfield2.ui.errorMessage);
  }, loadDelay);
}

// Load makes all the API calls needed to get the data to render the page
var loadData = function() {
  var notesP = Webfield2.getAll('/notes', {
    'content.authorids': user.profile.id,
    invitation: SUBMISSION_ID,
    details: 'replies',
    sort: 'number:desc',
    limit: CONSOLE_FETCH_LIMIT,
    domain: VENUE_ID
  });

  return notesP.then(function(notes) {
    var cameraReadyInvitationPromises = (notes || []).map(function(note) {
      return Webfield2.api.get('/invitations', {
        id: VENUE_ID + '/' + SUBMISSION_GROUP_NAME + note.number + '/-/' + CAMERA_READY_REVISION_NAME,
        domain: VENUE_ID,
        details: 'repliedNotes'
      }).then(function(result) {
        return result && result.invitations && result.invitations[0] || null;
      }, function() {
        return null;
      });
    });
    var invitationsP = cameraReadyInvitationPromises.length
      ? $.when.apply($, cameraReadyInvitationPromises).then(function() {
        return Array.prototype.slice.call(arguments).filter(Boolean);
      })
      : $.Deferred().resolve([]).promise();

    return $.when(
      $.Deferred().resolve(notes).promise(),
      invitationsP,
      Webfield2.api.get('/edges', { invitation: AE_RECOMMENDATION_ID, groupBy: 'head', domain: VENUE_ID})
      .then(function(result) { return result.groupedEdges; })
    );
  });
};

var formatData = function(notes, invitations, recommendationEdges) {

  var referrerUrl = encodeURIComponent('[Author Console](/group?id=' + VENUE_ID + '/' + AUTHOR_NAME + '#your-submissions)');
  notes = (notes || []).filter(function(submission) {
    return submission && submission.id && submission.content;
  });

  //build the rows
  var rows = [];
  var authoredPaperNumbers = new Set();
  var submissionUrlByNumber = notes.reduce(function(result, submission) {
    result[String(submission.number)] = appendRoleContext('/forum?id=' + encodeURIComponent(submission.id) + '&referrer=' + referrerUrl, 'author');
    return result;
  }, {});
  authoredSubmissionUrlByNumber = notes.reduce(function(result, submission) {
    result[String(submission.number)] = getLocationOrigin() + '/forum?id=' + encodeURIComponent(submission.id);
    return result;
  }, {});

  notes.map(function(submission) {
    authoredPaperNumbers.add(String(submission.number));
    var reviews =  Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, REVIEW_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var decisions =  Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, DECISION_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var decision = decisions.length && decisions[0];
    var submittedReviewCount = Number(submission.content.reviews_submitted_count && submission.content.reviews_submitted_count.value);
    if (!Number.isFinite(submittedReviewCount)) submittedReviewCount = reviews.length;
    var assignedReviewCount = Number(submission.content.reviews_assigned_count && submission.content.reviews_assigned_count.value);
    if (!Number.isFinite(assignedReviewCount)) {
      assignedReviewCount = Number(submission.content.reviews_required_count && submission.content.reviews_required_count.value);
    }
    if (!Number.isFinite(assignedReviewCount)) assignedReviewCount = reviews.length;
    var previousNumber = String(submission.content.previous_JMLR_submission_number && submission.content.previous_JMLR_submission_number.value || '').trim();
    var previousUrl = String(submission.content.previous_JMLR_submission_URL && submission.content.previous_JMLR_submission_URL.value || '').trim();
    var resolvedPreviousUrl = previousUrl && previousUrl !== 'N/A' ? previousUrl : submissionUrlByNumber[previousNumber];
    var roleContext = resolveConsolePaperRoleContext(submission, 'author', VENUE_ID + '/' + SUBMISSION_GROUP_NAME + submission.number + '/Authors');

    rows.push({
      submissionNumber: { number: submission.number},
      submission: {
        id: submission.id,
        number: submission.number,
        forum: submission.forum,
        content: Object.keys(submission.content).reduce(function(content, currentValue) {
          var value = submission.content[currentValue].value;
          if (shouldShowPreviousSubmissionField(currentValue, value)) {
            content[currentValue] = value;
          }
          return content;
        }, {}),
        previousSubmissionUrl: resolvedPreviousUrl,
        paperUrl: appendRoleContext('/forum?id=' + encodeURIComponent(submission.id) + '&referrer=' + referrerUrl, roleContext),
        roleContext: roleContext,
        referrer: referrerUrl
      },
      reviewProgressData: {
        noteId: submission.id,
        paperNumber: submission.number,
        reviews: reviews,
        submittedReviewCount: submittedReviewCount,
        assignedReviewCount: Math.max(assignedReviewCount, reviews.length),
        referrer: referrerUrl
      },
      paperStatusData: {
        status: deriveAuthorPaperStatus(submission, decision)
      }
    });

    //Add the assignment edges to each paper assignmnt invitation
    var paper_recommendation_invitation = invitations.find(function(i) { return i.id == Webfield2.utils.getInvitationId(VENUE_ID, submission.number, 'Recommendation', { prefix: ACTION_EDITORS_NAME, submissionGroupName: SUBMISSION_GROUP_NAME }); });
    if (paper_recommendation_invitation) {
      var foundEdges = recommendationEdges.find(function(a) { return a.id.head == submission.id; });
      if (foundEdges) {
        paper_recommendation_invitation.details.repliedEdges = foundEdges.values;
      }
    }
  });

  return applyConsoleModel({
    rows: rows,
    invitations: invitations.filter(function(invitation) {
      var match = invitation.id && invitation.id.match(new RegExp(VENUE_ID + '/' + SUBMISSION_GROUP_NAME + '([0-9]+)/-/' + CAMERA_READY_REVISION_NAME + '$'));
      return match && authoredPaperNumbers.has(match[1]);
    })
  }, 'author', { pendingTaskKeys: ['invitations'] });

};

var renderNewSubmissionButton = function() {
  ensureApi2FileChunkUpload();
  ensureSubmissionEditSignaturePost();

  $('#invitation').append(
    '<div id="new-submission" class="text-right" style="margin-bottom: 1rem;"></div>'
  );

  if (user && user.profile && user.profile.id && !_.startsWith(user.id, 'guest_')) {
    signedInProfile = user.profile;
    Webfield2.api.get('/profiles', { id: user.profile.id })
    .then(function(result) {
      var profile = result && result.profiles && result.profiles[0];
      if (profile) {
        signedInProfile = profile;
        updateSubmittingAuthorListGuidance($('.note_editor', '#new-submission'), signedInProfile);
      }
    });
  }

  Webfield2.get('/invitations', { id: SUBMISSION_ID })
  .then(function(result) {
    var submissionInvitation = result.invitations && result.invitations[0];
    if (!submissionInvitation) {
      return $.Deferred().reject('Submission invitation not found').promise();
    }

    var invitationForEditor = $.extend(true, {}, submissionInvitation);
    var ossField = invitationForEditor.edit &&
      invitationForEditor.edit.note &&
      invitationForEditor.edit.note.content &&
      invitationForEditor.edit.note.content.open_source_software;

    if (ossField && ossField.value && ossField.value.param) {
      ossField.value.param = $.extend(true, {}, ossField.value.param, {
        type: 'string',
        input: 'checkbox',
        enum: ['Yes']
      });
    }

    var buttonContainer = $('#new-submission');
    buttonContainer.hide().append(view.mkInvitationButton(invitationForEditor, function() {
      if (!user || _.startsWith(user.id, 'guest_')) {
        promptLogin(user);
        return;
      }

      if ($('.note_editor', buttonContainer).length) {
        $('.note_editor', buttonContainer).slideUp('normal', function() {
          $(this).remove();
        });
        return;
      }

      var profileId = user && user.profile && user.profile.id;
      var editorInvitation = $.extend(true, {}, invitationForEditor);
      if (profileId && _.startsWith(profileId, '~') && editorInvitation.edit) {
        editorInvitation.edit.signatures = [profileId];
      }

      view2.mkNewNoteEditor(editorInvitation, null, null, user, {
        onCompleted: function(editor) {
          if (editor) {
            editor.hide();
            ensureSubmissionEditorAlignment(editor);
            updateSubmittingAuthorListGuidance(editor, signedInProfile || (user && user.profile));
            relabelMainPaperPdf(editor);
            setupAuthorChangeDetection(editor);
            buttonContainer.append(editor);
            editor.slideDown();
          }
        },
        onValidate: function(invitationObj, formData) {
          var editor = $('.note_editor', buttonContainer);
          var authorChangeState = editor.data('authorChangeState');
          var profileId = user && user.profile && user.profile.id;
          var parsedAuthorList = parseAuthorListForSubmission(formData.author_list);
          if (parsedAuthorList.error) {
            return [parsedAuthorList.error];
          }
          var submittingAuthorError = validateSubmittingAuthorForSubmission(parsedAuthorList.authorids);
          if (submittingAuthorError) {
            return [submittingAuthorError];
          }
          formData.author_list = parsedAuthorList.authorList;
          formData.authors = parsedAuthorList.authors;
          formData.authorids = parsedAuthorList.authorids;
          if (profileId && _.startsWith(profileId, '~')) {
            formData.signatures = [profileId];
            formData.editSignatureInputValues = [profileId];
          }
          if (formData.open_source_software === 'Yes' ||
              (_.isArray(formData.open_source_software) && formData.open_source_software.indexOf('Yes') >= 0)) {
            formData.open_source_software = true;
          } else {
            delete formData.open_source_software;
          }
          if (!formData.pdf && !editor.find('input.note_pdf[type="file"]').first().prop('files').length) {
            return ['Main Paper PDF is required. Use the file chooser below Main Paper PDF to upload the main paper PDF before submitting.'];
          }
          var previousNumber = String(formData.previous_JMLR_submission_number || '').trim();
          if (previousNumber && previousNumber.toUpperCase() !== 'N/A') {
            if (!/^\d+$/.test(previousNumber)) {
              return ['Previous JMLR Submission Number must be a number, or N/A for a new submission.'];
            }
            formData.previous_JMLR_submission_number = previousNumber;
            if (authoredSubmissionUrlByNumber[previousNumber]) {
              formData.previous_JMLR_submission_URL = authoredSubmissionUrlByNumber[previousNumber];
            }
          }
          delete formData.author_change_confirmed;
          delete formData.author_change_approval_status;
          delete formData.author_change_summary;
          delete formData.previous_author_names;
          delete formData.current_author_names;
          return [];
        },
        onNoteCreated: function() {
          var authorConsoleUrl = '/group?id=' + VENUE_ID + '/' + AUTHOR_NAME + '&submissionPending=1#your-submissions';
          if (typeof globalThis !== 'undefined' && globalThis.location) {
            globalThis.location.href = authorConsoleUrl;
          } else if (typeof location !== 'undefined') {
            location.href = authorConsoleUrl;
          }
        }
      });
    }, { largeLabel: true }));

    return buttonContainer.fadeIn().promise();
  })
  .fail(function(error) {
    Webfield2.ui.errorMessage(error);
  });
};

var renderData = function(venueStatusData) {

  Webfield2.ui.renderTasks('#pending-tasks', venueStatusData.invitations, { referrer: encodeURIComponent('[Author Console](/group?id=' + VENUE_ID + '/' + AUTHOR_NAME + '#pending-tasks)') + '&t=' + Date.now()});

  Webfield2.ui.renderTable('#your-submissions', venueStatusData.rows, {
    headings: ['#', 'Paper Summary', 'Review Progress', 'Paper Status'],
    renders: [
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      function(data) {
        return Handlebars.templates.noteSummary(data) + renderJmlrSubmissionDetails(data);
      },
      function(data) {
        var reviews = data.reviews || [];
        var submittedReviewCount = Number(data.submittedReviewCount);
        if (!Number.isFinite(submittedReviewCount)) submittedReviewCount = reviews.length;
        var assignedReviewCount = Math.max(data.assignedReviewCount || 0, submittedReviewCount, reviews.length);
        return '<div class="reviewer-progress">' +
          '<span>Reviews ' + submittedReviewCount + '/' + assignedReviewCount + '</span>' +
          '</div>';
      },
      function(data) {
        return '<span>' + _.escape(data.status || 'Status unavailable') + '</span>';
      }
    ],
    extraClasses: 'console-table',
    postRenderTable: function() {
      $('#your-submissions .console-table th').eq(0).css('width', '4%'); // #
    }
  });

};


// Go!
main();
