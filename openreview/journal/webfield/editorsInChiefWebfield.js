// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var VENUE_ID = '.TMLR';
var SHORT_PHRASE = 'TMLR';
var SUBMISSION_ID = '.TMLR/-/Author_Submission';
var EDITORS_IN_CHIEF_NAME = 'Editors_In_Chief'
var REVIEWERS_NAME = 'Reviewers'
var ACTION_EDITOR_NAME = 'Action_Editors'
var EDITORS_IN_CHIEF_ID = VENUE_ID + '/' + EDITORS_IN_CHIEF_NAME
var HEADER = {
  title: 'TMLR Editors In Chief Console',
  instructions: 'Put instructions here'
};

var ae_url = '/edges/browse?traverse=.TMLR/Action_Editors/-/Assignment&edit=.TMLR/Action_Editors/-/Assignment&browse=.TMLR/Action_Editors/-/Affinity_Score;.TMLR/Action_Editors/-/Conflict&referrer=[Editors In Chief Console](/group?id=.TMLR/Editors_In_Chief)';
var reviewers_url = '/edges/browse?traverse=.TMLR/Reviewers/-/Assignment&edit=.TMLR/Reviewers/-/Assignment&browse=.TMLR/Reviewers/-/Affinity_Score;.TMLR/Reviewers/-/Conflict&referrer=[Editors In Chief Console](/group?id=.TMLR/Editors_In_Chief)';

HEADER.instructions = "<strong>Edge Browser:</strong><br><a href='" + ae_url + "'> Modify Action Editor Assignments</a><br><a href='" + reviewers_url + "'> Modify Reviewer Assignments</a> </p>";

// Main function is the entry point to the webfield code
var main = function() {

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Paper Status', 'Action Editor Status', 'Reviewer Status', 'test table'],
    referrer: args && args.referrer
  })

  loadData()
  .then(formatData)
  .then(renderData)
  .then(Webfield2.ui.done)
  .fail(Webfield2.ui.errorMessage);
};


var loadData = function() {

  return $.when(
    Webfield2.api.getGroupsByNumber(VENUE_ID, ACTION_EDITOR_NAME),
    Webfield2.api.getGroupsByNumber(VENUE_ID, REVIEWERS_NAME),
    Webfield2.api.getAllSubmissions(SUBMISSION_ID),
    Webfield2.api.getGroup(VENUE_ID + '/' + ACTION_EDITOR_NAME, { withProfiles: true}),
    Webfield2.api.getGroup(VENUE_ID + '/' + REVIEWERS_NAME, { withProfiles: true})
  );

}

var formatData = function(aeByNumber, reviewersByNumber, submissions, actionEditors, reviewers) {
  var referrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + EDITORS_IN_CHIEF_ID + '#paper-status)');

  var submissionsByNumber = _.keyBy(submissions, 'number');

  //build the rows
  var paperStatusRows = [];
  var reviewerStatusById = {};
  reviewers.members.forEach(function(reviewer, index) {
    reviewerStatusById[reviewer.id] = {
      index: { number: index + 1 },
      summary: {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
      },
      reviewerProgressData: {
        numCompletedReviews: 0,
        numPapers: 0,
        papers: [],
        referrer: referrerUrl
      },
      reviewerStatusData: {
        numCompletedReviews: 0,
        numPapers: 0,
        papers: [],
        referrer: referrerUrl
      }
    };
  });
  var actionEditorStatusById = {};
  actionEditors.members.forEach(function(actionEditor, index) {
    actionEditorStatusById[actionEditor.id] = {
      index: { number: index + 1 },
      summary: {
        id: actionEditor.id,
        name: actionEditor.name,
        email: actionEditor.email,
      },
      reviewProgressData: {
        numCompletedReviews: 0,
        numPapers: 0,
        papers: [],
        referrer: referrerUrl
      },
      decisionProgressData: {
        numCompletedMetaReviews: 0,
        papers: []
      }
    };
  });

  submissions.forEach(function(submission) {
    if (submission) {
      var number = submission.number;

      var reviews = submission.details.directReplies.filter(function(reply) {
        return reply.invitations.indexOf(VENUE_ID + '/Paper' + number + '/-/Review') >= 0;
      });
      var decisions = submission.details.directReplies.filter(function(reply) {
        return reply.invitations.indexOf(VENUE_ID + '/Paper' + number + '/-/Decision') >= 0;
      });
      var paperReviewers = reviewersByNumber[number];
      var paperActionEditors = aeByNumber[number];
      var paperReviewerStatus = {};
      var confidences = [];
      var completedReviews = reviews.length == paperReviewers.length;
      var formattedSubmission = { id: submission.id, number: number, forum: submission.forum, content: { title: submission.content.title.value, authors: submission.content.authors.value, authorids: submission.content.authorids.value}};

      paperReviewers.forEach(function(reviewer) {
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
        paperReviewerStatus[reviewer.anonId] = {
          id: reviewer.id,
          name: view.prettyId(reviewer.id),
          email: reviewer.id,
          completedReview: completedReview && true,
          forum: submission.id,
          note: completedReview && completedReview.id,
          status: status,
          forumUrl: 'https://openreview.net/forum?' + $.param({
            id: submission.id,
            noteId: submission.id,
            invitationId: VENUE_ID + '/Paper' + number + '/-/Review'
          })
        }
        var reviewerStatus = reviewerStatusById[reviewer.id];
        if (reviewerStatus) {
          reviewerStatus.reviewerProgressData.numPapers += 1;
          reviewerStatus.reviewerStatusData.numPapers += 1;
          reviewerStatus.reviewerProgressData.papers.push({ note: formattedSubmission, review: { forum: completedReview.forum, status: status }});
          reviewerStatus.reviewerStatusData.papers.push({
              note: formattedSubmission,
              numOfReviews: reviews.length,
              numOfReviewers: paperReviewers.length
          });
          if (completedReview){
            reviewerStatus.reviewerProgressData.numCompletedReviews += 1;
          }
          if (completedReviews) {
            reviewerStatus.reviewerStatusData.numCompletedReviews += 1;
          }
        }
      })

      paperActionEditors.forEach(function(actionEditor) {
        var completedDecision = decisions.find(function(decision) { return decision.signatures[0].endsWith('/Action_Editor_' + actionEditor.anonId); });
        var actionEditorStatus = actionEditorStatusById[actionEditor.id];
        if (actionEditorStatus) {
          actionEditorStatus.reviewProgressData.numPapers += 1;
          if (completedDecision){
            actionEditorStatus.decisionProgressData.numCompletedMetaReviews += 1;
          }
          if (completedReviews) {
            actionEditorStatus.reviewProgressData.numCompletedReviews += 1;
          }
          actionEditorStatus.reviewProgressData.papers.push({
              note: formattedSubmission,
              numOfReviews: reviews.length,
              numOfReviewers: paperReviewers.length
          });
          actionEditorStatus.decisionProgressData.papers.push({
            note: formattedSubmission,
            metaReview: completedDecision && { id: completedDecision.id, forum: submission.id, content: { recommendation: completedDecision.content.recommendation.value }}
        });
        }
      })

      var stats = {
        Confidence: {
          min: confidences.length ? _.min(confidences) : 'N/A',
          max: confidences.length ? _.max(confidences) : 'N/A',
          avg: confidences.length ? _.round(_.sum(confidences) / confidences.length, 2) : 'N/A'
        }
      };

      var metaReview = null;
      var decision = decisions.length && decisions[0];
      if (decision) {
        metaReview = { id: decision.id, forum: submission.id, content: { recommendation: decision.content.recommendation.value }};
      }

      paperStatusRows.push({
        checkbox: { selected: false, noteId: submission.id },
        submissionNumber: { number: number},
        submission: formattedSubmission,
        reviewProgressData: {
          noteId: submission.id,
          paperNumber: number,
          numSubmittedReviews: reviews.length,
          numReviewers: reviewers.length,
          reviewers: paperReviewerStatus,
          stats: stats,
          sendReminder: true,
        },
        areachairProgressData: {
          recommendation: metaReview && metaReview.content.recommendation,
          numMetaReview: metaReview ? 'One' : 'No',
          areachair: { name: paperActionEditors.map(function(ae) { return view.prettyId(ae.id); }), email: paperActionEditors.map(function(ae) { return ae.id; }) },
          metaReview: metaReview,
          referrer: referrerUrl
        },
        decision: submission.content.venue.value
      })
    }
  })

  return venueStatusData = {
    paperStatusRows: paperStatusRows,
    reviewerStatusRows: Object.values(reviewerStatusById),
    actionEditorStatusRows: Object.values(actionEditorStatusById)
  };
}

// Render functions
var renderData = function(venueStatusData) {

  Webfield2.ui.renderTable('#paper-status', venueStatusData.paperStatusRows, {
      headings: ['<input type="checkbox" id="select-all-papers">', '#', 'Paper Summary',
      'Review Progress', 'Action Editor Recommendation', 'Decision'],
      renders: [
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
        Handlebars.templates.noteAreaChairs,
        function(data) {
          return '<h4>' + data + '</h4>';
        },
      ],
      sortOptions: {
        Paper_Number: function(row) { return row.submissionNumber.number; },
        Paper_Title: function(row) { return _.toLower(_.trim(row.submission.content.title)); },
        Number_of_Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
        Number_of_Reviews_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedReviews; },
        Average_Confidence: function(row) { return row.reviewProgressData.stats.Confidence.avg === 'N/A' ? 0 : row.reviewProgressData.stats.Confidence.avg; },
        Max_Confidence: function(row) { return row.reviewProgressData.stats.Confidence.max === 'N/A' ? 0 : row.reviewProgressData.stats.Confidence.max; },
        Min_Confidence: function(row) { return row.reviewProgressData.stats.Confidence.min === 'N/A' ? 0 : row.reviewProgressData.stats.Confidence.min; },
        Recommendation: function(row) { return row.areachairProgressData.recommendation; },
        Decision: function(row) { return row.decision; }
      },
      searchProperties: {
        number: ['submissionNumber.number'],
        id: ['submission.id'],
        title: ['submission.content.title'],
        author: ['submission.content.authors','note.content.authorids'], // multi props
        keywords: ['submission.content.keywords'],
        reviewer: ['reviewProgressData.reviewers'],
        numReviewersAssigned: ['reviewProgressData.numReviewers'],
        numReviewsDone: ['reviewProgressData.numSubmittedReviews'],
        confidenceAvg: ['reviewProgressData.stats.Confidence.avg'],
        confidenceMax: ['reviewProgressData.stats.Confidence.max'],
        confidenceMin: ['reviewProgressData.stats.Confidence.min'],
        recommendation: ['areachairProgressData.recommendation'],
        decision: ['decision'],
        default: ['submissionNumber.number', 'submission.content.title']
      },
      reminderOptions: {
        container: 'a.send-reminder-link',
        defaultSubject: SHORT_PHRASE + ' Reminder',
        defaultBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the review page:\n\n{{submit_review_link}}' +
        '\n\nThank you,\n' + SHORT_PHRASE + ' Editor in Chief'
      },
      extraClasses: 'console-table paper-table',
      postRenderTable: function() {
        $('.console-table th').eq(0).css('width', '3%');
        $('.console-table th').eq(1).css('width', '5%');
        $('.console-table th').eq(2).css('width', '22%');
        $('.console-table th').eq(3).css('width', '30%');
        $('.console-table th').eq(4).css('width', '28%');
        $('.console-table th').eq(5).css('width', '12%');
      }
  })

  Webfield2.ui.renderTable('#reviewer-status', venueStatusData.reviewerStatusRows, {
    headings: ['#', 'Reviewer', 'Review Progress', 'Status'],
    renders: [
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      Handlebars.templates.committeeSummary,
      Handlebars.templates.notesReviewerProgress,
      Handlebars.templates.notesReviewerStatus
    ],
    sortOptions: {
      Reviewer_Name: function(row) { return row.summary.name.toLowerCase(); },
      Papers_Assigned: function(row) { return row.reviewerProgressData.numPapers; },
      Papers_with_Reviews_Missing: function(row) { return row.reviewerProgressData.numPapers - row.reviewerProgressData.numCompletedReviews; },
      Papers_with_Reviews_Submitted: function(row) { return row.reviewerProgressData.numCompletedReviews; },
      Papers_with_Completed_Reviews_Missing: function(row) { return row.reviewerStatusData.numPapers - row.reviewerStatusData.numCompletedReviews; },
      Papers_with_Completed_Reviews: function(row) { return row.reviewerStatusData.numCompletedReviews; }
    },
    searchProperties: {
      name: ['summary.name'],
      papersAssigned: ['reviewerProgressData.numPapers'],
      default: ['summary.name']
    },
    extraClasses: 'console-table'
  })

  Webfield2.ui.renderTable('#action-editor-status', venueStatusData.actionEditorStatusRows, {
    headings: ['#', 'Action Editor', 'Review Progress', 'Status'],
    renders: [
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      Handlebars.templates.committeeSummary,
      Handlebars.templates.notesAreaChairProgress,
      Handlebars.templates.notesAreaChairStatus
    ],
    sortOptions: {
      Action_Editor_Name: function(row) { return row.summary.name.toLowerCase(); },
      Papers_Assigned: function(row) { return row.reviewProgressData.numPapers; },
      Papers_with_Completed_Review_Missing: function(row) { return row.reviewProgressData.numPapers - row.reviewProgressData.numCompletedReviews; },
      Papers_with_Completed_Review: function(row) { return row.reviewProgressData.numCompletedReviews; },
      Papers_with_Completed_MetaReview_Missing: function(row) { return row.reviewProgressData.numPapers - row.reviewProgressData.numCompletedMetaReviews; },
      Papers_with_Completed_MetaReview: function(row) { return row.reviewProgressData.numCompletedMetaReviews; }
    },
    searchProperties: {
      name: ['summary.name'],
      papersAssigned: ['reviewProgressData.numPapers'],
      default: ['summary.name']
    },
    extraClasses: 'console-table'
  })

  var options = {
    sortOptions: {
      a: function(row) { return row.a.col1; }
    },
    searchProperties: {
      a: ['a.col1']
    }
  }

  Webfield2.ui.renderTable('#test-table', [
    { a: { col1: 'This is col 1'}, b: { c: 'this is col 2', d: 'this is col 2'}},
    { a: { col1: 'This is another col 1'}, b: { c: 'this is another col 2', d: 'this is another col 2'}}
  ], options);

}

main();
