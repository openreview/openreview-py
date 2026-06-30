// webfield_template
// Remove line above if you don't want this page to be overwriten

/* globals $: false */
/* globals _: false */
/* globals user: false */
/* globals args: false */
/* globals view: false */
/* globals Webfield2: false */

var VENUE_ID = 'JMLR';
var SHORT_PHRASE = {{VENUE_SHORT_NAME_JSON}};
var CONSOLE_FETCH_LIMIT = 100000;
var PUBLICATION_FETCH_LIMIT = 1000;
var PUBLICATION_EXPORT_ENABLED = {{PUBLICATION_EXPORT_ENABLED_JSON}};
var OPENREVIEW_PUBLICATION_ENABLED = {{OPENREVIEW_PUBLICATION_ENABLED_JSON}};
var CAMERA_READY_APPROVED = VENUE_ID + '/Camera_Ready_Approved';
var CAMERA_READY_PUBLISHED = VENUE_ID + '/Camera_Ready_Published';
var PUBLICATION_RETRACTED = VENUE_ID + '/Publication_Retracted';
var EDITORS_IN_CHIEF_ID = VENUE_ID + '/Editors_In_Chief';
var PRODUCTION_EDITORS_ID = VENUE_ID + '/Production_Editors';
var jmlrProductionEditorNotes = [];

var getContentValue = function(note, fieldName) {
  var field = note && note.content && note.content[fieldName];
  return field && Object.prototype.hasOwnProperty.call(field, 'value') ? field.value : field;
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
        pe: VENUE_ID + '/Production_Editors'
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
      pe: VENUE_ID + '/Production_Editors'
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

var normalizeIdentity = function(value) {
  return String(value || '').trim().toLowerCase();
};

var collectIdentityValues = function(profile) {
  var identities = [];
  var add = function(value) {
    if (value && Object.prototype.hasOwnProperty.call(value, 'value')) value = value.value;
    if (Array.isArray(value)) {
      value.forEach(add);
      return;
    }
    var normalized = normalizeIdentity(value);
    if (normalized && identities.indexOf(normalized) < 0) identities.push(normalized);
  };

  add(user && user.id);
  add(user && user.profile && user.profile.id);
  add(user && user.profile && user.profile.preferredEmail);
  add(user && user.profile && user.profile.emails);
  add(user && user.profile && user.profile.confirmedEmails);
  add(user && user.profile && user.profile.usernames);

  if (profile) {
    var content = profile.content || {};
    add(profile.id);
    add(profile.preferredEmail);
    add(profile.emails);
    add(profile.confirmedEmails);
    add(profile.usernames);
    add(content.preferredEmail);
    add(content.emails);
    add(content.confirmedEmails);
    add(content.usernames);
  }

  return identities;
};

var getProfile = function() {
  var profileId = user && user.profile && user.profile.id;
  if (!profileId) return $.Deferred().resolve(null).promise();
  return Webfield2.api.get('/profiles', { id: profileId })
    .then(function(result) {
      return result && result.profiles && result.profiles[0] || null;
    }, function() {
      return null;
    });
};

var textMatchesIdentity = function(text, identities) {
  var normalizedText = normalizeIdentity(text);
  return identities.some(function(identity) {
    return identity && normalizedText.indexOf(identity) >= 0;
  });
};

var isOperationallyConflicted = function(note, identities) {
  var authorids = getContentValue(note, 'authorids') || [];
  var authorList = getContentValue(note, 'author_list') || '';
  var declaredConflicts = getContentValue(note, 'conflict_of_interests') || '';
  return authorids.some(function(authorid) {
    return identities.indexOf(normalizeIdentity(authorid)) >= 0;
  }) || textMatchesIdentity(authorList, identities) || textMatchesIdentity(declaredConflicts, identities);
};

var statusLabel = function(note) {
  var venueId = getContentValue(note, 'venueid') || '';
  if (typeof JMLRPermissionHelpers !== 'undefined' && JMLRPermissionHelpers.getPublicationLifecycleLabel) {
    var publicationLabel = JMLRPermissionHelpers.getPublicationLifecycleLabel(venueId, VENUE_ID);
    if (publicationLabel) return publicationLabel;
  }
  return venueId ? view.prettyId(venueId.replace(VENUE_ID + '/', '')) : 'Submitted';
};

var isPublicationLifecycleNote = function(note) {
  var venueId = getContentValue(note, 'venueid') || '';
  return Boolean(note && note.number) && (
    venueId === CAMERA_READY_APPROVED ||
    venueId === CAMERA_READY_PUBLISHED ||
    venueId === PUBLICATION_RETRACTED
  );
};

var renderPaperTable = function(selector, notes, options) {
  options = options || {};
  if (!notes.length) {
    $(selector).html('<p class="empty-message">No items to display</p>');
    return;
  }
  var referrerUrl = encodeURIComponent('[Production Editor Console](/group?id=' + PRODUCTION_EDITORS_ID + ')');
  var rows = notes.map(function(note) {
    var title = getContentValue(note, 'title') || 'Untitled';
    var authors = getContentValue(note, 'authors') || [];
    var paperNumber = note.number ? 'Paper ' + note.number : 'Paper';
    var roleContext = resolveConsolePaperRoleContext(note, 'pe', VENUE_ID + '/Production_Editors');
    var paperUrl = appendRoleContext('/forum?id=' + encodeURIComponent(note.id) + '&referrer=' + referrerUrl, roleContext);
    return '<tr>' +
      '<td><a href="' + paperUrl + '">' + _.escape(paperNumber) + '</a></td>' +
      '<td><a href="' + paperUrl + '">' + _.escape(title) + '</a></td>' +
      '<td>' + _.escape(Array.isArray(authors) ? authors.join(', ') : authors) + '</td>' +
      '<td>' + _.escape(statusLabel(note)) + '</td>' +
    '</tr>';
  }).join('');
  $(selector).html(
    '<table class="table table-condensed table-striped">' +
      '<thead><tr><th>Paper</th><th>Title</th><th>Authors</th><th>Status</th></tr></thead>' +
      '<tbody>' + rows + '</tbody>' +
    '</table>'
  );
};

var renderLinkTab = function(selector, name, url) {
  $(selector).html('<p><a class="btn btn-default" href="' + _.escape(url) + '">' + _.escape(name) + '</a></p>');
};

var loadPublicationNotesByVenueId = function(venueId) {
  return Webfield2.api.get('/notes', {
    'content.venueid': venueId,
    details: 'replyCount,presentation',
    sort: 'mdate:desc',
    limit: PUBLICATION_FETCH_LIMIT,
    domain: VENUE_ID
  }).then(function(result) {
    return result && result.notes || [];
  });
};

var loadData = function() {
  return $.when(
    loadPublicationNotesByVenueId(CAMERA_READY_APPROVED),
    loadPublicationNotesByVenueId(CAMERA_READY_PUBLISHED),
    loadPublicationNotesByVenueId(PUBLICATION_RETRACTED),
    getProfile()
  );
};

var currentUserIsProductionEditor = function(productionEditorsGroup) {
  var members = productionEditorsGroup && productionEditorsGroup.members || [];
  var identities = collectIdentityValues();
  return identities.some(function(identity) {
    return members.indexOf(identity) >= 0;
  });
};

var renderData = function(approvedNotes, publishedNotes, retractedNotes, profile) {
  var identities = collectIdentityValues(profile);
  var notes = (approvedNotes || []).concat(publishedNotes || []).concat(retractedNotes || []);
  var operationalNotes = notes.filter(function(note) {
    return isPublicationLifecycleNote(note);
  }).filter(function(note) {
    return !isOperationallyConflicted(note, identities);
  });
  operationalNotes = applyConsoleModel({ rows: operationalNotes }, 'pe').rows;
  jmlrProductionEditorNotes = operationalNotes;
  renderPaperTable('#pending-publication', operationalNotes.filter(function(note) {
    return getContentValue(note, 'venueid') === CAMERA_READY_APPROVED;
  }));
  renderPaperTable('#published', operationalNotes.filter(function(note) {
    var venueId = getContentValue(note, 'venueid');
    return venueId === CAMERA_READY_PUBLISHED || venueId === PUBLICATION_RETRACTED;
  }));
};

var main = function() {
  var publicationInstructions = PUBLICATION_EXPORT_ENABLED && OPENREVIEW_PUBLICATION_ENABLED
    ? 'Open camera-ready approved papers to download publication files and mark them as published.'
    : PUBLICATION_EXPORT_ENABLED
      ? 'Open camera-ready approved papers to download publication files.'
      : 'Open camera-ready approved papers to manage publication status.';
  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: SHORT_PHRASE + ' Production Editor Console',
    instructions: publicationInstructions,
    tabs: ['Pending Publication', 'Published'],
    referrer: args && args.referrer
  });
  JMLRPermissionHelpers.renderVenueHomepageStrip({ container: '#group-container', venueId: VENUE_ID, $: $ });

  if (!user || user.isGuest) {
    Webfield2.ui.errorMessage('You must be logged in to access this page.');
    return;
  }

  Webfield2.api.getGroup(PRODUCTION_EDITORS_ID)
    .then(function(productionEditorsGroup) {
      if (!currentUserIsProductionEditor(productionEditorsGroup)) {
        Webfield2.ui.errorMessage('You must be a production editor to access this page.');
        return $.Deferred().reject().promise();
      }
      return loadData()
        .then(renderData)
        .then(Webfield2.ui.done);
    })
    .fail(function(error) {
      if (error) Webfield2.ui.errorMessage(error);
    });
};

main();
