// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var VENUE_ID = '.TMLR';
var SHORT_PHRASE = 'TMLR';
var SUBMISSION_ID = '.TMLR/-/Author_Submission';
var ACTION_EDITOR_NAME = 'Action_Editors'
var REVIEWERS_NAME = 'Reviewers'
var ACTION_EDITOR_ID = '.TMLR/Action_Editors'
var HEADER = {
  title: 'TMLR',
  instructions: 'Put instructions here'
};

// Main function is the entry point to the webfield code
var main = function() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(VENUE_ID);
  }

  renderHeader();

  Webfield2.utils.getPaperGroups(VENUE_ID, ACTION_EDITOR_NAME, { assigned: true })
  .then(loadData)
  .then(formatData)
  .then(renderTableAndTasks)
  .fail(function() {
    Webfield.ui.errorMessage();
  });
};


var loadData = function(assignedGroups) {

  var assignedPaperNumbers = Webfield2.utils.getPaperNumbersfromGroups(assignedGroups.paperGroups);
  return $.when(
    assignedPaperNumbers,
    assignedGroups,
    Webfield2.utils.getPaperGroups(VENUE_ID, REVIEWERS_NAME),
    Webfield2.utils.getAssignedInvitations(VENUE_ID, ACTION_EDITOR_NAME),
    Webfield2.utils.getSubmissions(SUBMISSION_ID, { numbers: assignedPaperNumbers})
  );
}

var formatData = function(assignedPaperNumbers, actionEditorGroups, reviewersGroups, invitations, submissions) {
  console.log(assignedPaperNumbers, actionEditorGroups, reviewersGroups, invitations, submissions);

  var submissionsByNumber = _.keyBy(submissions, 'number');
  var reviewersByNumber = {};

  reviewersGroups.paperGroups.forEach(function(group) {
    var number = Webfield2.utils.getNumberfromGroup(group.id, 'Paper');
    reviewersByNumber[number] = group.members;
  })

  //build the rows
  var rows = [];

  assignedPaperNumbers.forEach(function(number) {
    var submission = submissionsByNumber[number];
    if (submission) {

      var reviews = submission.details.directReplies.filter(function(reply) {
        return reply.invitations.indexOf(VENUE_ID + '/Paper' + number + '/-/Review') >= 0;
      });
      var reviewers = reviewersByNumber[number];

      rows.push([
        { selected: false, noteId: submission.id },
        { number: number},
        { forum: submission.forum, content: { title: submission.content.title.value, authors: submission.content.authors.value, authorids: submission.content.authorids.value}},
        { numSubmittedReviews: reviews.length, numReviewers: reviewers.length, reviewers: {} },
        {}
      ])
    }
  })


  return venueStatusData = {
    assignedPaperNumbers: assignedPaperNumbers,
    actionEditorGroups: actionEditorGroups,
    reviewersGroups: reviewersGroups,
    invitations: invitations,
    submissions: submissions,
    rows: rows
  };
}

// Render functions
var renderHeader = function() {
  Webfield.ui.setup('#group-container', VENUE_ID);
  Webfield.ui.header(HEADER.title, HEADER.instructions);

  var loadingMessage = '<p class="empty-message">Loading...</p>';
  var tabsList = [
    {
      heading: 'Assigned Papers',
      id: 'assigned-papers',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll',
      active: true
    },
    {
      heading: 'Action Editor Tasks',
      id: 'action-editor-tasks',
      content: loadingMessage
    }
  ];

  Webfield.ui.tabPanel(tabsList);
};


var renderTasks = function(invitations) {
  //  My Tasks tab
  var tasksOptions = {
    container: '#action-editor-tasks',
    emptyMessage: 'No outstanding tasks for this conference',
    referrer: encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + '#action-editor-tasks)')
  }
  $(tasksOptions.container).empty();

  Webfield.ui.newTaskList(invitations, [], tasksOptions);
  $('.tabs-container a[href="#action-editor-tasks"]').parent().show();
}

var renderTableAndTasks = function(venueStatusData) {

  renderTasks(venueStatusData.invitations);

  Webfield2.ui.renderTable('#assigned-papers', ['<input type="checkbox" id="select-all-papers">', '#', 'Paper Summary',
  'Review Progress', 'Decision Status'], [
    function(data) {
      var checked = data.selected ? 'checked="checked"' : '';
      return '<label><input type="checkbox" class="select-note-reviewers" data-note-id="' +
        data.noteId + '" ' + checked + '></label>';
    },
    function(data) {
      return '<strong class="note-number">' + data.number + '</strong>';
    },
    Handlebars.templates.noteSummary,
    Handlebars.templates.noteReviewers,
    Handlebars.templates.noteMetaReviewStatus
  ], venueStatusData.rows)

  registerEventHandlers();

  Webfield.ui.done();
}

// Event Handlers
var registerEventHandlers = function() {
}




main();
