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

  Webfield2.utils.getGroupsByNumber(VENUE_ID, ACTION_EDITOR_NAME, { assigned: true })
  .then(loadData)
  .then(formatData)
  .then(renderTableAndTasks)
  .fail(function() {
    Webfield.ui.errorMessage();
  });
};


var loadData = function(assignedGroups) {

  return $.when(
    assignedGroups,
    Webfield2.utils.getGroupsByNumber(VENUE_ID, REVIEWERS_NAME),
    Webfield2.utils.getAssignedInvitations(VENUE_ID, ACTION_EDITOR_NAME),
    Webfield2.utils.getSubmissions(SUBMISSION_ID, { numbers: Object.keys(assignedGroups)})
  );
}

var formatData = function(assignedGroups, reviewersByNumber, invitations, submissions) {
  var referrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + '#assigned-papers)');

  var submissionsByNumber = _.keyBy(submissions, 'number');

  //build the rows
  var rows = [];

  Object.keys(assignedGroups).forEach(function(number) {
    var submission = submissionsByNumber[number];
    if (submission) {

      var reviews = submission.details.directReplies.filter(function(reply) {
        return reply.invitations.indexOf(VENUE_ID + '/Paper' + number + '/-/Review') >= 0;
      });
      var decision = submission.details.directReplies.find(function(reply) {
        return reply.invitations.indexOf(VENUE_ID + '/Paper' + number + '/-/Decision') >= 0;
      });
      var reviewers = reviewersByNumber[number];
      var reviewerStatus = {};
      var confidences = []

      reviewers.forEach(function(reviewer) {
        var completedReview = reviews.find(function(review) { return review.signatures[0].endsWith('/Reviewer_' + reviewer.anonId); });
        var status = {};
        if (completedReview) {
          var confidenceString = completedReview.content.confidence.value;
          var confidence = parseInt(confidenceString.substring(0, confidenceString.indexOf(':')));
          confidences.push(confidence);
          status = {
            Recommendation: completedReview.content.recommendation.value,
            Confidence: confidence,
            'Review length': completedReview.content.review.value.length
          }
        }
        reviewerStatus[reviewer.anonId] = {
          id: reviewer.id,
          name: view.prettyId(reviewer.id),
          email: reviewer.id,
          completedReview: completedReview && true,
          forum: submission.id,
          note: completedReview && completedReview.id,
          status: status
        }
      })

      var stats = {
        Confidence: {
          min: confidences.length ? _.min(confidences) : 'N/A',
          max: confidences.length ? _.max(confidences) : 'N/A',
          avg: confidences.length ? _.round(_.sum(confidences) / confidences.length, 2) : 'N/A'
        }
      };

      rows.push({
        checked: { selected: false, noteId: submission.id },
        number: { number: number},
        note: { forum: submission.forum, content: { title: submission.content.title.value, authors: submission.content.authors.value, authorids: submission.content.authorids.value}},
        reviewProgressData: {
          numSubmittedReviews: reviews.length,
          numReviewers: reviewers.length,
          reviewers: reviewerStatus,
          stats: stats
        },
        actionEditorData: {
          recommendation: decision && decision.content.recommendation.value,
          editUrl: decision ? ('/forum?id=' + submission.id + '&noteId=' + decision.id + '&referrer=' + referrerUrl) : null
        }
      })
    }
  })


  return venueStatusData = {
    invitations: invitations,
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
  ], venueStatusData.rows, {
      sortOptions: {
        Paper_Number: function(row) { return row.number.number; },
        Paper_Title: function(row) { return _.toLower(_.trim(row.note.content.title)); },
        Number_of_Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
        Number_of_Reviews_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedReviews; },
        Average_Confidence: function(row) { return row.reviewProgressData.stats.Confidence.avg === 'N/A' ? 0 : row.reviewProgressData.stats.Confidence.avg; },
        Max_Confidence: function(row) { return row.reviewProgressData.stats.Confidence.max === 'N/A' ? 0 : row.reviewProgressData.stats.Confidence.max; },
        Min_Confidence: function(row) { return row.reviewProgressData.stats.Confidence.min === 'N/A' ? 0 : row.reviewProgressData.stats.Confidence.min; },
        Recommendation: function(row) { return row.actionEditorData.recommendation; }
      },
      searchProperties: {
        number: ['number.number'],
        id: ['note.id'],
        title: ['note.content.title'],
        author: ['note.content.authors','note.content.authorids'], // multi props
        keywords: ['note.content.keywords'],
        reviewer: ['reviewProgressData.reviewers'],
        numReviewersAssigned: ['reviewProgressData.numReviewers'],
        numReviewsDone: ['reviewProgressData.numSubmittedReviews'],
        confidenceAvg: ['reviewProgressData.stats.Confidence.avg'],
        confidenceMax: ['reviewProgressData.stats.Confidence.max'],
        confidenceMin: ['reviewProgressData.stats.Confidence.min'],
        recommendation: ['actionEditorData.recommendation']
      }
  })

  registerEventHandlers();

  Webfield.ui.done();
}

// Event Handlers
var registerEventHandlers = function() {
}




main();
