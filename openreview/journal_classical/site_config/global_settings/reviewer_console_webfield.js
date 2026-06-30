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
var CONSOLE_FETCH_LIMIT = 100000;
var HEADER = {
  title: SHORT_PHRASE + ' Reviewer Console',
  instructions: 'Visit the <a href="https://' + WEBSITE + '" target="_blank" rel="nofollow"> ' + SHORT_PHRASE + ' website</a> for the reviewer guidelines.'
};
var REVIEWERS_NAME = 'Reviewers';
var REVIEW_NAME = 'Review';
var ACTION_EDITORS_NAME = '';
var DECISION_NAME = 'Decision';
var SUBMISSION_GROUP_NAME = 'Paper';
var REVIEWERS_ID = VENUE_ID + '/' + REVIEWERS_NAME;
var REVIEWERS_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Assignment';
var REVIEWERS_REVIEW_DUE_DATE_ID = REVIEWERS_ID + '/-/Review_Due_Date';
var REVIEWERS_CUSTOM_MAX_PAPERS_NAME = 'Custom_Max_Papers';
var REVIEWERS_AVAILABILITY_NAME = 'Assignment_Availability';
var REVIEWERS_EXPERTISE_SELECTION_ID = REVIEWERS_ID + '/-/Expertise_Selection';
var REVIEWERS_EXPERT_REVIEWER_LISTING_PREFERENCE_NAME = 'Expert_Reviewer_Listing_Preference';
var REVIEWERS_EXPERT_REVIEWER_LISTING_PREFERENCE_ID = REVIEWERS_ID + '/-/' + REVIEWERS_EXPERT_REVIEWER_LISTING_PREFERENCE_NAME;
var EXPERT_REVIEWER_STATE_ID = VENUE_ID + '/Expert_Reviewer_State';
var REVIEWER_NEW_ASSIGNMENT_COOLDOWN_DAYS = {{REVIEWER_NEW_ASSIGNMENT_COOLDOWN_DAYS}};
var assignedPapersReferrerUrl = encodeURIComponent('[Reviewer Console](/group?id=' + VENUE_ID + '/' + REVIEWERS_NAME + '#assigned-papers)');
var pendingTasksReferrerUrl = encodeURIComponent('[Reviewer Console](/group?id=' + VENUE_ID + '/' + REVIEWERS_NAME + '#pending-tasks)');
var referrerUrl = assignedPapersReferrerUrl;

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

var hideOpenReviewGroupModeBanner = function() {
  if (!$('#jmlr-hide-group-mode-banner').length) {
    $('head').append('<style id="jmlr-hide-group-mode-banner">#edit-banner { display: none !important; }</style>');
  }
  $('#edit-banner').hide();
};

var addIdentityValue = function(ids, value) {
  if (!value) return;
  if (Array.isArray(value)) {
    value.forEach(function(item) { addIdentityValue(ids, item); });
    return;
  }
  if (value && Object.prototype.hasOwnProperty.call(value, 'value')) {
    addIdentityValue(ids, value.value);
    return;
  }
  var normalized = String(value).toLowerCase();
  if (normalized && ids.indexOf(normalized) < 0) ids.push(normalized);
};

var profileIdentityValues = function(profile) {
  var ids = [];
  if (!profile) return ids;
  addIdentityValue(ids, profile._memberId);
  var content = profile.content || {};
  addIdentityValue(ids, profile.id);
  addIdentityValue(ids, profile.preferredEmail);
  addIdentityValue(ids, profile.emails);
  addIdentityValue(ids, profile.confirmedEmails);
  addIdentityValue(ids, profile.usernames);
  addIdentityValue(ids, content.preferredEmail);
  addIdentityValue(ids, content.emails);
  addIdentityValue(ids, content.confirmedEmails);
  addIdentityValue(ids, content.usernames);
  return ids;
};

var currentUserIdentityValues = function(activeProfile) {
  var ids = [];
  addIdentityValue(ids, user && user.id);
  addIdentityValue(ids, user && user.profile && user.profile.id);
  addIdentityValue(ids, user && user.profile && user.profile.preferredEmail);
  addIdentityValue(ids, user && user.profile && user.profile.emails);
  addIdentityValue(ids, user && user.profile && user.profile.confirmedEmails);
  addIdentityValue(ids, user && user.profile && user.profile.usernames);
  profileIdentityValues(activeProfile).forEach(function(id) { addIdentityValue(ids, id); });
  return ids;
};

var fetchProfile = function(profileId) {
  if (!String(profileId || '').match(/^~.*\d$/)) return $.Deferred().resolve({ id: profileId }).promise();
  return Webfield2.api.get('/profiles', { id: profileId }).then(function(result) {
    var profile = result && result.profiles && result.profiles[0] || { id: profileId };
    profile._memberId = profileId;
    return profile;
  }, function() {
    return { id: profileId, _memberId: profileId };
  });
};

var getGroupMembers = function(groupResult) {
  var result = Array.isArray(groupResult) ? groupResult[0] : groupResult;
  var group = result && result.groups && result.groups[0] || result && result.group || result || {};
  var members = group.members || group.content && group.content.members && group.content.members.value || [];
  return Array.isArray(members) ? members : [];
};

var getRoleMemberId = function(profile) {
  return profile && (profile._memberId || profile.id);
};

var rolePersonKey = function(profileId) {
  return String(profileId || '')
    .replace(/^~/, '')
    .replace(/\d+$/, '')
    .replace(/_(AE|Action_Editor|ActionEditor|Reviewer|Reviewers|Editor|EIC|Author|II|III|IV|V|VI|VII|VIII|IX|X)$/i, '')
    .replace(/_(AE|Action_Editor|ActionEditor|Reviewer|Reviewers|Editor|EIC|Author)$/ig, '')
    .toLowerCase();
};

var uniqueValues = function(values) {
  return values.filter(function(value, index) {
    return value && values.indexOf(value) === index;
  });
};

var isPersonIdentityId = function(id) {
  return /^~.*\d$/.test(String(id || '')) || /@/.test(String(id || ''));
};

var currentSignatureId = function() {
  return user && user.profile && (user.profile.preferredId || user.profile.id) || user && user.id;
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

var resolveConsoleRoleProfileId = function(roleGroupId, preferredPattern) {
  var activeProfileId = user && user.profile && user.profile.id;
  var activeProfilePromise = activeProfileId ? fetchProfile(activeProfileId) : $.Deferred().resolve(null).promise();
  return $.when(
    Webfield2.api.get('/groups', { id: roleGroupId, limit: 1, select: 'members' }),
    activeProfilePromise
  ).then(function(groupResult, activeProfile) {
    var members = getGroupMembers(groupResult);
    var currentIds = currentUserIdentityValues(activeProfile);
    var memberPromises = members.map(fetchProfile);
    if (!memberPromises.length) return activeProfileId || user.id;
    return $.when.apply($, memberPromises).then(function() {
      var profiles = Array.prototype.slice.call(arguments);
      if (memberPromises.length === 1) profiles = [arguments[0]];
      var candidates = profiles.filter(function(profile) {
        if (!isPersonIdentityId(getRoleMemberId(profile))) return false;
        var profileIds = profileIdentityValues(profile);
        return profileIds.some(function(id) { return currentIds.indexOf(id) >= 0; });
      });
      if (!candidates.length && activeProfileId && members.indexOf(activeProfileId) >= 0) return activeProfileId;
      if (!candidates.length) return null;
      var preferred = candidates.find(function(profile) {
        return preferredPattern.test(getRoleMemberId(profile) || '') || preferredPattern.test(profile.id || '');
      });
      if (preferred) return getRoleMemberId(preferred);
      var candidateKeys = candidates.map(function(profile) {
        return rolePersonKey(getRoleMemberId(profile));
      }).filter(Boolean);
      var samePersonPreferred = profiles.find(function(profile) {
        return preferredPattern.test(getRoleMemberId(profile) || '') &&
          candidateKeys.indexOf(rolePersonKey(getRoleMemberId(profile))) >= 0;
      });
      return getRoleMemberId(samePersonPreferred || candidates[0]);
    });
  });
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

var getReviewProgressCounts = function(submission) {
  var submitted = Number(submission.content && submission.content.reviews_submitted_count && submission.content.reviews_submitted_count.value);
  var required = Number(submission.content && submission.content.reviews_required_count && submission.content.reviews_required_count.value);
  return {
    submitted: Number.isFinite(submitted) ? submitted : null,
    required: Number.isFinite(required) ? required : null
  };
};

var renderReviewProgressCount = function(counts) {
  if (!counts || counts.submitted === null && counts.required === null) return '';
  var submitted = counts.submitted === null ? '?' : counts.submitted;
  var required = counts.required === null ? '?' : counts.required;
  return '<p class="small text-muted" style="margin-top: 6px;">Reviews submitted: ' +
    _.escape(String(submitted)) + '/' + _.escape(String(required)) + '</p>';
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

var reviewInvitationPaperNumber = function(invitation) {
  if (!invitation) return null;
  var replytoNote = invitation.details && invitation.details.replytoNote;
  if (replytoNote && replytoNote.number) return String(replytoNote.number);
  var match = String(invitation.id || '').match(new RegExp('^' + VENUE_ID + '/' + SUBMISSION_GROUP_NAME + '(\\d+)/-/' + REVIEW_NAME + '$'));
  return match ? match[1] : null;
};

var isReviewerAssignmentEdge = function(edge) {
  var invitationId = String(edge && edge.invitation || '');
  return invitationId == REVIEWERS_ASSIGNMENT_ID || /\/Paper[0-9]+\/Reviewers\/-\/Assignment$/.test(invitationId);
};

var edgesForTail = function(edges, tail) {
  return (edges || []).filter(function(edge) {
    return edge && edge.tail === tail;
  });
};

var activeAssignmentForumIds = function(assignmentEdges) {
  return uniqueValues((assignmentEdges || []).filter(function(edge) {
    return edge && !edge.ddate && edge.head && isReviewerAssignmentEdge(edge);
  }).map(function(edge) {
    return edge.head;
  }));
};

var activeAssignmentPaperNumbers = function(assignmentEdges) {
  return uniqueValues((assignmentEdges || []).filter(function(edge) {
    return edge && !edge.ddate && isReviewerAssignmentEdge(edge);
  }).map(function(edge) {
    var match = String(edge.invitation || '').match(new RegExp('^' + VENUE_ID + '/' + SUBMISSION_GROUP_NAME + '(\\d+)/' + REVIEWERS_NAME + '/-/Assignment$'));
    return match && match[1] || null;
  }).filter(Boolean));
};

var reviewerPaperNumbersFromAnonGroups = function(groups) {
  return uniqueValues((groups || []).map(function(group) {
    var groupId = String(group && group.id || '');
    if (isReviewerSystemInputGroupId(groupId)) return null;
    var match = groupId.match(new RegExp('^' + VENUE_ID + '/' + SUBMISSION_GROUP_NAME + '(\\d+)/Reviewer_'));
    return match && match[1] || null;
  }).filter(Boolean));
};

var submissionsForForumIds = function(forumIds) {
  var promises = (forumIds || []).map(function(forumId) {
    return Webfield2.api.get('/notes', {
      id: forumId,
      details: 'replies',
      domain: VENUE_ID
    }).then(function(result) {
      return result && result.notes && result.notes[0] || null;
    }, function() {
      return null;
    });
  });
  if (!promises.length) return $.Deferred().resolve([]).promise();
  return $.when.apply($, promises).then(function() {
    return Array.prototype.slice.call(arguments).filter(Boolean);
  });
};

var reviewInvitationsForPaperNumbers = function(numbers) {
  var promises = (numbers || []).map(function(number) {
    return Webfield2.api.get('/invitations', {
      id: VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/-/' + REVIEW_NAME,
      type: 'notes',
      domain: VENUE_ID
    }).then(function(result) {
      return result && result.invitations && result.invitations[0] || null;
    }, function() {
      return null;
    });
  });
  if (!promises.length) return $.Deferred().resolve([]).promise();
  return $.when.apply($, promises).then(function() {
    return Array.prototype.slice.call(arguments).filter(Boolean);
  });
};

var activeReviewerAssignmentEdgeForSubmission = function(assignmentEdges, submission) {
  var forumId = submission && (submission.forum || submission.id);
  var paperScopedAssignmentId = VENUE_ID + '/Paper' + submission.number + '/Reviewers/-/Assignment';
  return (assignmentEdges || []).filter(function(edge) {
    return edge && !edge.ddate && edge.head == forumId && isReviewerAssignmentEdge(edge);
  }).sort(function(a, b) {
    if (a.invitation === paperScopedAssignmentId && b.invitation !== paperScopedAssignmentId) return -1;
    if (b.invitation === paperScopedAssignmentId && a.invitation !== paperScopedAssignmentId) return 1;
    return Number(b.cdate || b.tcdate || 0) - Number(a.cdate || a.tcdate || 0);
  })[0] || null;
};

var reviewerAssignmentDueDateMillis = function(edge) {
  return null;
};

var activeReviewerDueDateEdgeForSubmission = function(dueDateEdges, submission) {
  var forumId = submission && (submission.forum || submission.id);
  return (dueDateEdges || []).filter(function(edge) {
    return edge && !edge.ddate && edge.head == forumId;
  }).sort(function(a, b) {
    return Number(b.cdate || b.tcdate || 0) - Number(a.cdate || a.tcdate || 0);
  })[0] || null;
};

var reviewerDueDateMillis = function(assignmentEdge, dueDateEdge) {
  if (dueDateEdge && dueDateEdge.weight) return Number(dueDateEdge.weight);
  return reviewerAssignmentDueDateMillis(assignmentEdge);
};

var reviewerAssignedPaperNumbers = function(assignedGroups, assignedInvitations) {
  var numbers = Object.keys(assignedGroups || {});
  (assignedInvitations || []).forEach(function(invitation) {
    var number = reviewInvitationPaperNumber(invitation);
    if (number && numbers.indexOf(number) < 0) numbers.push(number);
  });
  return numbers;
};

var filterAssignedSubmissions = function(submissions, assignedNumbers, assignmentForumIds) {
  var numberSet = assignedNumbers.reduce(function(acc, number) {
    acc[String(number)] = true;
    return acc;
  }, {});
  var forumSet = assignmentForumIds.reduce(function(acc, forumId) {
    acc[String(forumId)] = true;
    return acc;
  }, {});
  return (submissions || []).filter(function(submission) {
    return numberSet[String(submission.number)] || forumSet[String(submission.forum || submission.id)];
  });
};


function main() {
  ensureApi2ApiUrl();
  hideOpenReviewGroupModeBanner();

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Pending Tasks', 'Active Papers', 'Assigned Papers'],
    referrer: args && args.referrer
  })
  JMLRPermissionHelpers.renderVenueHomepageStrip({ container: '#group-container', venueId: VENUE_ID, $: $ });

  loadData()
  .then(formatData)
  .then(renderData)
  .then(Webfield2.ui.done)
  .fail(Webfield2.ui.errorMessage);
}

// Load makes all the API calls needed to get the data to render the page
var loadData = function() {

  return resolveConsoleRoleProfileId(REVIEWERS_ID, /Reviewer/i)
  .then(function(consoleProfileId) {
    return (consoleProfileId ? Webfield2.api.getAll('/edges', {
      tail: consoleProfileId,
      domain: VENUE_ID
    }) : $.Deferred().resolve([]).promise())
    .then(function(assignmentEdges) {
    assignmentEdges = edgesForTail(assignmentEdges, consoleProfileId);
    var assignedAnonGroupsPromise = consoleProfileId ? Webfield2.api.getAll('/groups', {
      prefix: VENUE_ID + '/' + SUBMISSION_GROUP_NAME,
      member: consoleProfileId,
      select: 'id,members',
      domain: VENUE_ID
    }).then(function(groups) {
      return groups || [];
    }) : $.Deferred().resolve([]).promise();
    return assignedAnonGroupsPromise.then(function(assignedAnonGroups) {
    var assignmentForumIds = activeAssignmentForumIds(assignmentEdges);
    var assignedNumbers = uniqueValues(activeAssignmentPaperNumbers(assignmentEdges).concat(reviewerPaperNumbersFromAnonGroups(assignedAnonGroups)));
    var submissionsByNumberPromise = assignedNumbers.length
      ? Webfield2.api.getAllSubmissions(SUBMISSION_ID, { numbers: assignedNumbers, details: 'replies', domain: VENUE_ID, limit: CONSOLE_FETCH_LIMIT})
      : $.Deferred().resolve([]).promise();
    var submissionsByForumPromise = submissionsForForumIds(assignmentForumIds);
    var submissionsPromise = $.when(submissionsByNumberPromise, submissionsByForumPromise).then(function(numberSubmissions, forumSubmissions) {
      var seen = {};
      return (numberSubmissions || []).concat(forumSubmissions || []).filter(function(submission) {
        var id = submission && (submission.forum || submission.id);
        if (!id || seen[id]) return false;
        seen[id] = true;
        return true;
      });
    });
    var assignedInvitationsPromise = reviewInvitationsForPaperNumbers(assignedNumbers);
    return $.when(
      $.Deferred().resolve({}).promise(),
      Webfield2.api.getGroupsByNumber(VENUE_ID, ACTION_EDITORS_NAME),
      assignedInvitationsPromise,
      submissionsPromise.then(function(submissions) {
        return filterAssignedSubmissions(submissions, assignedNumbers, assignmentForumIds);
      }),
      Webfield2.api.getAll('/invitations', {
        id: REVIEWERS_ID + '/-/' + REVIEWERS_AVAILABILITY_NAME,
        type: 'edges'
      }).then(function(invitations) {
        return invitations[0];
      }),
      Webfield2.api.getAll('/invitations', {
        id: REVIEWERS_ID + '/-/' + REVIEWERS_CUSTOM_MAX_PAPERS_NAME,
        type: 'edges'
      }).then(function(invitations) {
        return invitations[0];
      }),
      Webfield2.api.getAll('/invitations', {
        id: REVIEWERS_EXPERT_REVIEWER_LISTING_PREFERENCE_ID,
        type: 'edges'
      }).then(function(invitations) {
        return invitations[0];
      }),
      consoleProfileId ? Webfield2.api.getAll('/edges', {
        invitation: REVIEWERS_ID + '/-/' + REVIEWERS_AVAILABILITY_NAME,
        tail: consoleProfileId
      }).then(function(edges) {
        return edges && edges[0];
      }) : $.Deferred().resolve(null).promise(),
      consoleProfileId ? Webfield2.api.getAll('/edges', {
        invitation: REVIEWERS_ID + '/-/' + REVIEWERS_CUSTOM_MAX_PAPERS_NAME,
        tail: consoleProfileId
      }).then(function(edges) {
        return edges && edges[0];
      }) : $.Deferred().resolve(null).promise(),
      consoleProfileId ? Webfield2.api.getAll('/edges', {
        invitation: REVIEWERS_EXPERT_REVIEWER_LISTING_PREFERENCE_ID,
        tail: consoleProfileId
      }).then(function(edges) {
        return edges && edges[0];
      }) : $.Deferred().resolve(null).promise(),
      $.Deferred().resolve(assignedAnonGroups).promise(),
      consoleProfileId ? Webfield2.api.getAll('/edges', {
        invitation: REVIEWERS_REVIEW_DUE_DATE_ID,
        tail: consoleProfileId,
        domain: VENUE_ID
      }) : $.Deferred().resolve([]).promise(),
      assignmentEdges,
      consoleProfileId
    );
    })
    })
  })
}

var isReviewerSystemInputAnonId = function(anonId) {
  return ['Scoring_Input', 'Matching_Input'].indexOf(String(anonId || '')) >= 0;
};

var isReviewerSystemInputGroupId = function(groupId) {
  return ['Reviewer_Scoring_Input', 'Reviewer_Matching_Input'].indexOf(String(groupId || '').split('/').pop()) >= 0;
};

var reviewerAnonIdFromGroupId = function(groupId, number) {
  var prefix = VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Reviewer_';
  if (!groupId || groupId.indexOf(prefix) !== 0 || isReviewerSystemInputGroupId(groupId)) return null;
  return groupId.slice(prefix.length);
};

var formatData = function(assignedGroups, actionEditorsByNumber, invitations, submissions, availabilityInvitation, customQuotaInvitation, expertListingPreferenceInvitation, availabilityEdge, customQuotaEdge, expertListingPreferenceEdge, assignedAnonGroups, dueDateEdges, assignmentEdges, consoleProfileId) {

  //build the rows
  var rows = [];
  var pendingTasks = [];

  submissions.forEach(function(submission) {
    submission.details = submission.details || {};
    submission.details.replies = submission.details.replies || [];

    var number = submission.number;
    var roleContext = resolveConsolePaperRoleContext(submission, 'reviewer', VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Reviewers');
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
    var assignedReviewers = assignedGroups[number] || assignedGroups[String(number)] || [];
    var assignedGroup = assignedReviewers.find(function(group) {
      return group.id == consoleProfileId && group.anonId && !isReviewerSystemInputAnonId(group.anonId);
    });
    if (!assignedGroup && consoleProfileId) {
      var readableAnonGroup = (assignedAnonGroups || []).find(function(group) {
        return (group.members || []).indexOf(consoleProfileId) >= 0 && reviewerAnonIdFromGroupId(group.id, number);
      });
      if (readableAnonGroup) {
        assignedGroup = {
          id: consoleProfileId,
          anonId: reviewerAnonIdFromGroupId(readableAnonGroup.id, number),
          anonymousGroupId: readableAnonGroup.id
        };
      }
    }
    var reviewerSignature = assignedGroup ? VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Reviewer_' + assignedGroup.anonId : null;
    var reviewInvitationId = VENUE_ID + '/Paper' + number + '/-/' + REVIEW_NAME;
    var reviewReplies = submission.details && submission.details.replies || [];
    var review = reviewerSignature ? reviewReplies.find(function(reply) {
      return (reply.invitations || []).indexOf(reviewInvitationId) >= 0 &&
        reply.signatures &&
        reply.signatures[0] == reviewerSignature;
    }) : null;
    var decisions =  Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, DECISION_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var decision = decisions.length && decisions[0];
    var reviewProgressCounts = getReviewProgressCounts(submission);
    var reviewInvitation = invitations.find(function(invitation) { return invitation.id == reviewInvitationId; });
    if (!reviewInvitation && reviewerSignature && !decision) {
      reviewInvitation = {
        id: reviewInvitationId,
        cdate: submission.cdate
      };
    }
    if (reviewInvitation && !review) {
      var reviewerAssignmentEdge = activeReviewerAssignmentEdgeForSubmission(assignmentEdges, submission);
      var reviewerDueDateEdge = activeReviewerDueDateEdgeForSubmission(dueDateEdges, submission);
      pendingTasks.push({
        submissionNumber: number,
        submissionTitle: formattedSubmission.content.title,
        name: REVIEW_NAME,
        duedate: reviewerDueDateMillis(reviewerAssignmentEdge, reviewerDueDateEdge) || JMLRPermissionHelpers.getReviewerEffectiveDueDate(reviewInvitation),
        cdate: reviewInvitation.cdate,
        roleContext: roleContext,
        url: appendRoleContext('/forum?id=' + encodeURIComponent(submission.forum || submission.id) + '&referrer=' + pendingTasksReferrerUrl, roleContext),
        actionUrl: appendRoleContext('/forum?id=' + submission.forum + '&noteId=' + submission.forum + '&invitationId=' + reviewInvitation.id + '&referrer=' + pendingTasksReferrerUrl, roleContext)
      });
    }
    var reviewInvitationUrl = reviewInvitation && appendRoleContext('/forum?id=' + submission.forum + '&noteId=' + submission.forum + '&invitationId=' + reviewInvitation.id + '&referrer=' + referrerUrl, roleContext);
    var reviewEditUrl = review && appendRoleContext('/forum?id=' + submission.forum + '&noteId=' + review.id + '&referrer=' + referrerUrl, roleContext);
    formattedSubmission.paperUrl = reviewEditUrl || reviewInvitationUrl || formattedSubmission.paperUrl;

    rows.push({
      submissionNumber: { number: number},
      submission: ({
        ...formattedSubmission,
        beyondPdf: submission.content.beyond_pdf?.value !== undefined
      }),
      reviewStatus: {
        invitationUrl: reviewInvitationUrl,
        review: review,
        editUrl: reviewEditUrl,
        progressCounts: reviewProgressCounts
      },
      actionEditorData: {
        recommendation: decision && decision.content.recommendation.value,
        url: decision ? appendRoleContext('/forum?id=' + submission.id + '&noteId=' + decision.id + '&referrer=' + referrerUrl, roleContext) : null
      }
    })
  })

  if (availabilityInvitation) {
    availabilityInvitation.details = {
      repliedEdges: availabilityEdge ? [availabilityEdge] : [],
    }
  }

  if (customQuotaInvitation) {
    customQuotaInvitation.details = {
      repliedEdges: customQuotaEdge ? [customQuotaEdge] : [],
    }
  }

  if (expertListingPreferenceInvitation) {
    expertListingPreferenceInvitation.details = {
      repliedEdges: expertListingPreferenceEdge ? [expertListingPreferenceEdge] : [],
    }
  }


  return applyConsoleModel({
    invitations: invitations,
    rows: rows,
    activeRows: rows.filter(function(row) {
      return row.actionEditorData && !row.actionEditorData.recommendation;
    }),
    pendingTasks: pendingTasks,
    availabilityInvitation: availabilityInvitation,
    customQuotaInvitation: customQuotaInvitation,
    expertListingPreferenceInvitation: expertListingPreferenceInvitation,
    consoleProfileId: consoleProfileId
  }, 'reviewer', { rowKeys: ['rows', 'activeRows'], pendingTaskKeys: ['pendingTasks'] });

}

var getPendingTaskLabel = function(task) {
  return 'Paper ' + task.submissionNumber + (task.submissionTitle ? ': ' + task.submissionTitle : '');
};

var getPendingTaskActionLabel = function(task) {
  var labelByName = {};
  labelByName[REVIEW_NAME] = 'Submit review';
  return labelByName[task.name] || task.name.replace(/_/g, ' ');
};

var getPendingTaskDueDate = function(task) {
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

var renderPendingTasks = function(container, tasks) {
  $(container).empty();
  if (!tasks.length) {
    $(container).append('<p>No pending tasks for this venue</p>');
    return;
  }

  var sortedTasks = tasks.slice().sort(function(a, b) {
    return (a.duedate || a.cdate || 0) - (b.duedate || b.cdate || 0);
  });
  var list = $('<ul class="list-unstyled"></ul>');
  sortedTasks.forEach(function(task) {
    var item = $('<li></li>');
    var primaryLine = $('<div class="reviewer-pending-task-primary"></div>');
    primaryLine.append($('<a></a>').attr('href', task.actionUrl || task.url).attr('target', '_blank').text(getPendingTaskLabel(task)));
    primaryLine.append($('<span></span>').text(getPendingTaskDueDate(task)));
    item.append(primaryLine);
    if (task.actionUrl) {
      var actionLine = $('<div class="reviewer-pending-task-actions" style="margin-top: 4px;"></div>');
      actionLine.append($('<a class="btn btn-xs btn-default"></a>').attr('href', task.actionUrl).attr('target', '_blank').text(getPendingTaskActionLabel(task)));
      item.append(actionLine);
    }
    list.append(item);
  });
  $(container).append(list);
};

var renderReviewerNoteSummary = function(data) {
  var html = Handlebars.templates.noteSummary(data);
  if (!data || !data.paperUrl) return html;
  return html.replace(/href="\/forum\?id=[^"]+"/, 'href="' + _.escape(data.paperUrl) + '"');
};

var getNextMonthStartOption = function() {
  var now = new Date();
  var timestamp = Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1);
  return {
    value: timestamp,
    label: new Date(timestamp).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
  };
};

var getMonthStartOptions = function(count) {
  var now = new Date();
  var options = [];
  for (var offset = 1; offset <= count; offset++) {
    var timestamp = Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + offset, 1);
    options.push({
      value: timestamp,
      label: new Date(timestamp).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
    });
  }
  return options;
};

var getAvailabilityState = function(edge, allowIndefinite) {
  if (!edge || edge.label !== 'Unavailable') return 'available';
  if (edge.weight && Number(edge.weight) > Date.now()) return 'until';
  if (edge.weight && Number(edge.weight) <= Date.now()) return 'available';
  return allowIndefinite ? 'indefinite' : 'available';
};

var getAvailabilityStatusText = function(edge) {
  var state = getAvailabilityState(edge, true);
  if (state === 'until') return 'Current setting: unavailable until ' + formatDate(Number(edge.weight)) + '.';
  if (state === 'indefinite') return 'Current setting: unavailable indefinitely.';
  return 'Current setting: available for new assignments.';
};

var renderAvailabilityForm = function(container, config) {
  var edge = config.edge || null;
  var state = getAvailabilityState(edge, true);
  var monthOptions = getMonthStartOptions(6);
  var selectedMonthValue = state === 'until' ? Number(edge.weight) : null;
  if (selectedMonthValue && !monthOptions.some(function(option) { return option.value === selectedMonthValue; })) {
    monthOptions.push({
      value: selectedMonthValue,
      label: formatDate(selectedMonthValue)
    });
    monthOptions.sort(function(a, b) { return a.value - b.value; });
  }
  var currentStatus = getAvailabilityStatusText(edge);
  var monthOptionsHtml = monthOptions.map(function(option) {
    return '<option value="' + option.value + '"' + (selectedMonthValue === option.value ? ' selected' : '') + '>Unavailable until ' + _.escape(option.label) + '</option>';
  }).join('');

  $(container).append(
    '<details class="assignment-availability-form panel panel-default" style="max-width: 720px; margin: 12px 0;">' +
      '<summary class="panel-heading" style="cursor: pointer;">' +
        '<strong>Assignment Availability</strong>' +
        '<span class="small text-muted js-availability-current" style="margin-left: 8px;">' + _.escape(currentStatus) + '</span>' +
      '</summary>' +
      '<div class="panel-body">' +
        '<p class="text-muted">' + _.escape(config.description) + '</p>' +
        '<div class="form-inline">' +
          '<label for="' + config.idPrefix + '-availability-state" style="margin-right: 6px;">Status:</label>' +
          '<select id="' + config.idPrefix + '-availability-state" class="form-control js-availability-state" style="margin-right: 8px;">' +
            '<option value="available"' + (state === 'available' ? ' selected' : '') + '>Available</option>' +
            monthOptionsHtml +
            '<option value="indefinite"' + (state === 'indefinite' ? ' selected' : '') + '>Unavailable indefinitely</option>' +
          '</select>' +
          '<button type="button" class="btn btn-primary js-save-availability">Save</button>' +
        '</div>' +
        '<p class="small text-muted js-availability-month-help" style="margin-top: 8px;">Unavailable pauses resume at the beginning of the selected month. Reviewers can also pause new assignments indefinitely.</p>' +
        '<p class="js-availability-status" style="margin-top: 8px;"></p>' +
      '</div>' +
    '</details>'
  );

  var form = $(container).find('.assignment-availability-form').last();

  form.find('.js-save-availability').on('click', function() {
    var button = $(this);
    var status = form.find('.js-availability-status');
    var selectedState = form.find('.js-availability-state').val();
    var edgePayload = {
      invitation: config.invitationId,
      signatures: [config.signatureId || config.tailId],
      readers: uniqueValues(['JMLR/Editors_In_Chief', 'JMLR/Action_Editors', config.tailId]),
      writers: uniqueValues(['JMLR/Editors_In_Chief', config.tailId]),
      head: config.headId,
      tail: config.tailId,
      label: selectedState === 'available' ? 'Available' : 'Unavailable'
    };
    if (config.edgeId) edgePayload.id = config.edgeId;
    if (selectedState !== 'available' && selectedState !== 'indefinite') edgePayload.weight = Number(selectedState);
    button.prop('disabled', true).text('Saving...');
    status.removeClass('text-danger text-success').text('');
    Webfield2.api.post('/edges', edgePayload).then(function(postedEdge) {
      config.edgeId = postedEdge.id;
      config.edge = postedEdge;
      form.find('.js-availability-current').text(getAvailabilityStatusText(postedEdge));
      status.addClass('text-success').text('Assignment availability saved.');
    }, function(error) {
      var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to save assignment availability.';
      status.addClass('text-danger').text(message);
    }).always(function() {
      button.prop('disabled', false).text('Save');
    });
  });
};

var renderReviewerConsoleControlsIntro = function(container) {
  $(container).append(
    '<div class="reviewer-console-controls-intro" style="max-width: 720px; margin: 12px 0;">' +
      '<p><strong>Max Active Reviews:</strong> Maximum number of active JMLR papers assigned to you at one time. Once this limit is reached, new papers will not be assigned, but prior-round resubmissions may still be reassigned.</p>' +
      '<p class="small text-muted"><strong>New-paper cooldown:</strong> After a new review assignment, ordinary new papers are paused for ' + _.escape(REVIEWER_NEW_ASSIGNMENT_COOLDOWN_DAYS) + ' days. Valid resubmission continuity may still be handled through checked assignment logic.</p>' +
    '</div>'
  );
};

var getCustomQuotaValue = function(edge, fallback) {
  if (edge && edge.weight !== undefined && edge.weight !== null) return Number(edge.weight);
  return fallback;
};

var renderCustomQuotaForm = function(container, config) {
  var currentValue = getCustomQuotaValue(config.edge, config.defaultValue);
  var optionHtml = [];
  for (var value = 1; value <= 15; value++) {
    optionHtml.push(
      '<option value="' + value + '"' + (Number(currentValue) === value ? ' selected' : '') + '>' + value + '</option>'
    );
  }

  $(container).append(
    '<details class="custom-max-reviews-form panel panel-default" style="max-width: 720px; margin: 12px 0;">' +
      '<summary class="panel-heading" style="cursor: pointer;">' +
        '<strong>Max Active Reviews</strong>' +
        '<span class="small text-muted js-custom-max-reviews-current" style="margin-left: 8px;">Current setting: ' + _.escape(String(currentValue)) + '</span>' +
      '</summary>' +
      '<div class="panel-body">' +
        '<div class="form-inline">' +
          '<label for="reviewer-max-active-reviews" style="margin-right: 6px;">Maximum:</label>' +
          '<select id="reviewer-max-active-reviews" class="form-control js-custom-max-reviews" style="margin-right: 8px;">' +
            optionHtml.join('') +
          '</select>' +
          '<button type="button" class="btn btn-primary js-save-custom-max-reviews">Save</button>' +
        '</div>' +
        '<p class="small text-muted" style="margin-top: 8px;">This limits ordinary new review assignments. Prior-round resubmissions may still be reassigned through checked continuity logic.</p>' +
        '<p class="js-custom-max-reviews-status" style="margin-top: 8px;"></p>' +
      '</div>' +
    '</details>'
  );

  var form = $(container).find('.custom-max-reviews-form').last();
  form.find('.js-save-custom-max-reviews').on('click', function() {
    var button = $(this);
    var status = form.find('.js-custom-max-reviews-status');
    var edgePayload = {
      invitation: config.invitationId,
      signatures: [config.signatureId || config.tailId],
      readers: uniqueValues(['JMLR/Editors_In_Chief', config.headId, config.tailId]),
      writers: uniqueValues(['JMLR/Editors_In_Chief', config.tailId]),
      head: config.headId,
      tail: config.tailId,
      weight: Number(form.find('.js-custom-max-reviews').val())
    };
    if (config.edgeId) edgePayload.id = config.edgeId;

    button.prop('disabled', true).text('Saving...');
    status.removeClass('text-danger text-success').text('');
    Webfield2.api.post('/edges', edgePayload).then(function(postedEdge) {
      config.edgeId = postedEdge.id;
      config.edge = postedEdge;
      form.find('.js-custom-max-reviews-current').text('Current setting: ' + postedEdge.weight);
      status.addClass('text-success').text('Max Active Reviews saved.');
    }, function(error) {
      var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to save Max Active Reviews.';
      status.addClass('text-danger').text(message);
    }).always(function() {
      button.prop('disabled', false).text('Save');
    });
  });
};

var renderExpertiseSelectionLink = function(container) {
  $(container).append(
    '<div class="expertise-selection-link panel panel-default" style="max-width: 720px; margin: 12px 0;">' +
      '<div class="panel-body">' +
        '<p style="margin-bottom: 6px;"><strong>Expertise Selection:</strong></p>' +
        '<a href="/invitation?id=' + REVIEWERS_EXPERTISE_SELECTION_ID + '&referrer=' + referrerUrl + '">Select your expertise</a>' +
      '</div>' +
    '</div>'
  );
};

var getExpertReviewerListingPreferenceLabel = function(edge) {
  return edge && edge.label === 'Opt_Out' ? 'Current setting: do not list me publicly.' : 'Current setting: list me publicly if I qualify.';
};

var renderExpertReviewerListingPreferenceForm = function(container, config) {
  var edge = config.edge || null;
  var currentValue = edge && edge.label === 'Opt_Out' ? 'Opt_Out' : 'List';
  $(container).append(
    '<details class="expert-reviewer-listing-preference-form panel panel-default" style="max-width: 720px; margin: 12px 0;">' +
      '<summary class="panel-heading" style="cursor: pointer;">' +
        '<strong>Top Reviewer Listing</strong>' +
        '<span class="small text-muted js-expert-reviewer-listing-current" style="margin-left: 8px;">' + _.escape(getExpertReviewerListingPreferenceLabel(edge)) + '</span>' +
      '</summary>' +
      '<div class="panel-body">' +
        '<div class="form-inline">' +
          '<label for="expert-reviewer-listing-preference" style="margin-right: 6px;">Public listing:</label>' +
          '<select id="expert-reviewer-listing-preference" class="form-control js-expert-reviewer-listing-preference" style="margin-right: 8px;">' +
            '<option value="List"' + (currentValue === 'List' ? ' selected' : '') + '>List me publicly if I qualify</option>' +
            '<option value="Opt_Out"' + (currentValue === 'Opt_Out' ? ' selected' : '') + '>Do not list me publicly</option>' +
          '</select>' +
          '<button type="button" class="btn btn-primary js-save-expert-reviewer-listing-preference">Save</button>' +
        '</div>' +
        '<p class="small text-muted" style="margin-top: 8px;">This controls only public Top Reviewer recognition. It does not affect review assignments, availability, load, cooldown, or permissions.</p>' +
        '<p class="js-expert-reviewer-listing-preference-status" style="margin-top: 8px;"></p>' +
      '</div>' +
    '</details>'
  );

  var form = $(container).find('.expert-reviewer-listing-preference-form').last();
  form.find('.js-save-expert-reviewer-listing-preference').on('click', function() {
    var button = $(this);
    var status = form.find('.js-expert-reviewer-listing-preference-status');
    var selectedLabel = form.find('.js-expert-reviewer-listing-preference').val();
    var edgePayload = {
      invitation: config.invitationId,
      signatures: [config.signatureId || config.tailId],
      readers: uniqueValues([VENUE_ID + '/Editors_In_Chief', config.tailId]),
      writers: uniqueValues([VENUE_ID + '/Editors_In_Chief', config.tailId]),
      head: config.headId,
      tail: config.tailId,
      label: selectedLabel
    };
    var expireExistingPreference = config.edgeId ? Webfield2.api.post('/edges', $.extend({}, edgePayload, {
      id: config.edgeId,
      ddate: Date.now()
    })) : $.Deferred().resolve(null).promise();

    button.prop('disabled', true).text('Saving...');
    status.removeClass('text-danger text-success').text('');
    expireExistingPreference.then(function() {
      return Webfield2.api.post('/edges', edgePayload);
    }).then(function(postedEdge) {
      config.edgeId = postedEdge.id;
      config.edge = postedEdge;
      form.find('.js-expert-reviewer-listing-current').text(getExpertReviewerListingPreferenceLabel(postedEdge));
      status.addClass('text-success').text('Top Reviewer listing preference saved.');
    }, function(error) {
      var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to save Top Reviewer listing preference.';
      status.addClass('text-danger').text(message);
    }).always(function() {
      button.prop('disabled', false).text('Save');
    });
  });
};

var renderData = function(venueStatusData) {
  renderReviewerConsoleControlsIntro('#invitation');

  if (venueStatusData.customQuotaInvitation && venueStatusData.consoleProfileId) {
    renderCustomQuotaForm('#invitation', {
      invitationId: REVIEWERS_ID + '/-/' + REVIEWERS_CUSTOM_MAX_PAPERS_NAME,
      headId: REVIEWERS_ID,
      tailId: venueStatusData.consoleProfileId,
      edgeId: venueStatusData.customQuotaInvitation.details && venueStatusData.customQuotaInvitation.details.repliedEdges[0] && venueStatusData.customQuotaInvitation.details.repliedEdges[0].id,
      edge: venueStatusData.customQuotaInvitation.details && venueStatusData.customQuotaInvitation.details.repliedEdges[0],
      defaultValue: {{REVIEWERS_MAX_PAPERS}}
    });
  }

  if (venueStatusData.availabilityInvitation && venueStatusData.consoleProfileId) {
    renderAvailabilityForm('#invitation', {
      idPrefix: 'reviewer',
      invitationId: REVIEWERS_ID + '/-/' + REVIEWERS_AVAILABILITY_NAME,
      headId: REVIEWERS_ID,
      tailId: venueStatusData.consoleProfileId,
      edgeId: venueStatusData.availabilityInvitation.details && venueStatusData.availabilityInvitation.details.repliedEdges[0] && venueStatusData.availabilityInvitation.details.repliedEdges[0].id,
      edge: venueStatusData.availabilityInvitation.details && venueStatusData.availabilityInvitation.details.repliedEdges[0],
      allowIndefinite: true,
      description: 'Use this to pause new JMLR review assignments. You will still keep any papers already assigned to you.'
    });
  }

  if (venueStatusData.expertListingPreferenceInvitation && venueStatusData.consoleProfileId) {
    renderExpertReviewerListingPreferenceForm('#invitation', {
      invitationId: REVIEWERS_EXPERT_REVIEWER_LISTING_PREFERENCE_ID,
      headId: EXPERT_REVIEWER_STATE_ID,
      tailId: venueStatusData.consoleProfileId,
      edgeId: venueStatusData.expertListingPreferenceInvitation.details && venueStatusData.expertListingPreferenceInvitation.details.repliedEdges[0] && venueStatusData.expertListingPreferenceInvitation.details.repliedEdges[0].id,
      edge: venueStatusData.expertListingPreferenceInvitation.details && venueStatusData.expertListingPreferenceInvitation.details.repliedEdges[0]
    });
  }

  renderExpertiseSelectionLink('#invitation');

  renderPendingTasks('#pending-tasks', venueStatusData.pendingTasks);
  renderReviewerPapersTable('#active-papers', venueStatusData.activeRows);
  renderReviewerPapersTable('#assigned-papers', venueStatusData.rows);
}

var renderReviewerPapersTable = function(container, rows) {
  Webfield2.ui.renderTable(container, rows, {
    headings: ['#', 'Paper Summary', 'Your Review', 'Decision Status'],
    renders: [
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      function(data) {
        var noteSummary = renderReviewerNoteSummary(data);
        var beyondPdfTag = data.beyondPdf ? '<span class="badge" style="background-color: #3f6978">Beyond PDF</span>' : '';
        return noteSummary + beyondPdfTag + renderPreviousSubmissionLink(data) + renderJmlrSubmissionDetails(data);
      },
      function(data) {
        if (data.review) {
          var recommendationHtml = '';
          if (data.review.content && data.review.content.recommendation_for_acceptance) {
            recommendationHtml = '<h4>Recommendation:</h4>' +
            '<p>' + data.review.content.recommendation_for_acceptance.value + '</p>';
          }
          return '<div>' +
          recommendationHtml +
          '<p>' +
            '<a href="' + data.editUrl + '" target="_blank">Read ' + REVIEW_NAME+ '</a>' +
          '</p>' +
          renderReviewProgressCount(data.progressCounts) +
          '</div>';
        } else if (data.invitationUrl) {
          return '<h4><a href="' + data.invitationUrl + '" target="_blank">Submit ' + REVIEW_NAME + '</a></h4>' +
            renderReviewProgressCount(data.progressCounts);
        }
        return '<div>' + renderReviewProgressCount(data.progressCounts) + '</div>'
      },
      function(data) {
        if (data.recommendation) {
          return '<div>' +
          '<h4>Action Editor Decision:</h4>' +
          '<p>' +
            '<strong>' + data.recommendation + '</strong>' +
          '</p>' +
          '<p>' +
            '<a href="' + data.url + '" target="_blank">Read</a>' +
          '</p>' +
          '</div>'
        }
        return '<div><h4><strong>No decision yet</strong></h4></div>'
      }
    ],
    extraClasses: 'console-table',
    postRenderTable: function() {
      $(container + ' .console-table th').eq(0).css('width', '4%'); // #
    }
  })
};


// Go!
main();
