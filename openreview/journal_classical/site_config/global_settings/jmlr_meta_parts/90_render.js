var loadPeopleManagementData = function() {
  return $.when(
    Webfield2.api.getGroup(ACTION_EDITOR_ID, { withProfiles: true }),
    Webfield2.api.getGroup(REVIEWERS_ID, { withProfiles: true }),
    OSS_ACTION_EDITORS_ENABLED ? getGroupSafe(OSS_ACTION_EDITORS_ID, { withProfiles: true }) : $.Deferred().resolve({ members: [] }).promise(),
    getGroupSafe(EXPERT_REVIEWERS_ID, { withProfiles: true }),
    getGroupSafe(PRODUCTION_EDITORS_ID, { withProfiles: true }),
    Webfield2.api.getGroup(EDITORS_IN_CHIEF_ID, { withProfiles: true }),
    getEdgesByTailMap(ACTION_EDITORS_AVAILABILITY_ID, ACTION_EDITOR_ID),
    getEdgesByTailMap(REVIEWERS_AVAILABILITY_ID, REVIEWERS_ID)
  ).then(formatPeopleManagementData);
};

var renderPeopleManagementPage = function() {
  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: SHORT_PHRASE + ' People Management',
    instructions: 'Shared operational page for ' + SHORT_PHRASE + ' role management and recruitment.',
    tabs: ['Bulk Invite', 'Assign Roles'],
    fullWidth: true
  });

  if (!user || user.isGuest) {
    Webfield2.ui.errorMessage('You must be logged in to access this page.');
    return;
  }

  $.when(
    Webfield2.api.getGroup(EDITORS_IN_CHIEF_ID)
  ).then(function(eicGroup) {
    if (!userCanManagePeople(eicGroup)) {
      Webfield2.ui.errorMessage('Only ' + SHORT_PHRASE + ' Editors-in-Chief can access people management.');
      return;
    }
    jmlrPeopleManagementSignature = EDITORS_IN_CHIEF_ID;
    loadPeopleManagementData()
      .then(function(data) {
        renderBulkInviteTab(data);
        renderAssignRolesTab(data);
      })
      .then(Webfield2.ui.done)
      .fail(Webfield2.ui.errorMessage);
  }).fail(Webfield2.ui.errorMessage);
};

var renderVenueSubmissionRoute = function() {
  $('#your-consoles').closest('.tab-pane').hide();
  $('a[href="#your-consoles"]').closest('li').hide();
  $('#jmlr-submission-route').closest('#jmlr-venue-actions').hide();
  if (!$('#new-submission').length) {
    $('#group-container').append(
      '<div id="new-submission" class="text-right" style="margin-bottom: 1rem;"></div>'
    );
  }
  return renderVenueSubmissionEditor({ onlyWhenRoute: true });
};

var installVenueSubmissionRouteHandler = function() {
  if (typeof globalThis === 'undefined' || !globalThis.addEventListener) return;
  $(globalThis)
    .off('hashchange.jmlrVenueSubmission')
    .on('hashchange.jmlrVenueSubmission', function() {
      if (!isVenueSubmissionRoute()) return;
      renderVenueSubmissionRoute()
        .then(Webfield2.ui.done)
        .fail(Webfield2.ui.errorMessage);
    });
};

var main = function() {
  if (args && args.peopleManagement) {
    renderPeopleManagementPage();
    return;
  }

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: VENUE_DISPLAY_NAME,
    instructions: INSTRUCTIONS,
    tabs: ['Your Consoles'],
    fullWidth: false
  });
  hideVenueGroupChrome();
  installVenueSubmissionRouteHandler();
  if (isVenueSubmissionRoute()) {
    renderVenueSubmissionRoute()
      .then(Webfield2.ui.done)
      .fail(Webfield2.ui.errorMessage);
    return;
  }

  renderVenueSubmissionRouteButton();

  if (!user || user.isGuest) {
    $('#your-consoles').html(
      '<p class="text-muted">Log in to view your ' + _.escape(SHORT_PHRASE) + ' role consoles.</p>'
    );
    Webfield2.ui.done();
    return;
  }

  var ids = currentUserIds();
  $.when.apply($, ROLE_CONSOLES.map(function(consoleConfig) {
    return consoleVisibleForUser(consoleConfig, ids);
  }))
    .then(function() {
      renderConsoles(Array.prototype.slice.call(arguments).filter(Boolean));
    })
    .then(renderReviewerVolunteerRouteButton)
    .then(Webfield2.ui.done)
    .fail(Webfield2.ui.errorMessage);
};

main();
