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

var isActionEditorAssignmentEdge = function(edge) {
  var invitationId = String(edge && edge.invitation || '');
  return invitationId == ACTION_EDITOR_ID + '/-/Assignment' || /\/Paper[0-9]+\/Action_Editors\/-\/Assignment$/.test(invitationId);
};

var activeActionEditorAssignmentPaperNumbers = function(assignmentEdges) {
  return uniqueValues((assignmentEdges || []).filter(function(edge) {
    return edge && !edge.ddate && isActionEditorAssignmentEdge(edge);
  }).map(function(edge) {
    var match = String(edge.invitation || '').match(new RegExp('^' + VENUE_ID + '/' + SUBMISSION_GROUP_NAME + '(\\d+)/' + ACTION_EDITOR_NAME + '/-/Assignment$'));
    return match && match[1] || null;
  }).filter(Boolean));
};

var actionEditorPaperNumbersFromAnonGroups = function(groups) {
  return uniqueValues((groups || []).map(function(group) {
    var match = String(group && group.id || '').match(new RegExp('^' + VENUE_ID + '/' + SUBMISSION_GROUP_NAME + '(\\d+)/Action_Editor_'));
    return match && match[1] || null;
  }).filter(Boolean));
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


// Helpers
