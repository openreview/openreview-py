// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var CONFERENCE_ID = '';
var HEADER = {};
var SENIOR_AREA_CHAIR_NAME = '';
var WILDCARD_INVITATION = CONFERENCE_ID + '.*';

var conferenceStatusData = {};

// Main function is the entry point to the webfield code
var main = function() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID);
  }

  renderHeader();

  getRootGroups()
  .then(loadData)
  .then(formatData)
  .then(renderTableAndTasks)
  .fail(function() {
    Webfield.ui.errorMessage();
  });
};

var renderHeader = function() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);
  Webfield.ui.header(HEADER.title, HEADER.instructions);

  var loadingMessage = '<p class="empty-message">No assigned Area Chairs.</p>';
  var tabsList = [
    {
      heading: 'Assigned Area Chairs',
      id: 'assigned-areachairs',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll',
      active: true
    },
    {
      heading: 'Senior Area Chair Tasks',
      id: 'senior-areachair-tasks',
      content: loadingMessage
    }
  ];

  Webfield.ui.tabPanel(tabsList);
};

var getRootGroups = function() {
  // Get paper groups or assignments

  return $.Deferred().resolve([]);

};

var loadData = function(papers) {

  var invitationsP = Webfield.getAll('/invitations', {
    regex: WILDCARD_INVITATION,
    invitee: true,
    duedate: true,
    type: 'all',
    details: 'replytoNote,repliedNotes,repliedTags,repliedEdges'
  })
  .then(function(invitations) {
    return _.filter(invitations, function(inv) {
      return _.get(inv, 'reply.replyto') || _.get(inv, 'reply.referent') || _.has(inv, 'reply.content.head') || _.has(inv, 'reply.content.tag');
    });
  });

  return $.when(
    invitationsP
  );
};

var formatData = function(invitations) {
  conferenceStatusData = {
    invitations: invitations
  };

  return $.Deferred().resolve(conferenceStatusData);
};

var renderTasks = function(invitations) {
  //  My Tasks tab
  var tasksOptions = {
    container: '#senior-areachair-tasks',
    emptyMessage: 'No outstanding tasks for this conference',
    referrer: encodeURIComponent('[Senior Area Chair Console](/group?id=' + CONFERENCE_ID + '/' + SENIOR_AREA_CHAIR_NAME + '#senior-areachair-tasks)')
  }
  $(tasksOptions.container).empty();

  Webfield.ui.newTaskList(invitations, [], tasksOptions);
  $('.tabs-container a[href="#senior-areachair-tasks"]').parent().show();
}

var renderTableAndTasks = function(conferenceStatusData) {
  renderTasks(conferenceStatusData.invitations);

  registerEventHandlers();

  Webfield.ui.done();
}

// Event Handlers
var registerEventHandlers = function() {
};


main();
