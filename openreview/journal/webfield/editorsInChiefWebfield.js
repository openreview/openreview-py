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
  instructions: ''
};

// Main function is the entry point to the webfield code
var main = function() {

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Paper Status', 'Action Editor Status', 'Reviewer Status'],
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
        metaReviewName: 'Decision',
        numPapers: 0,
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
      var recommendations = submission.details.directReplies.filter(function(reply) {
        return reply.invitations.indexOf(VENUE_ID + '/Paper' + submission.number + '/-/Official_Recommendation') >= 0;
      });
      var recommendationByReviewer = {};
      recommendations.forEach(function(recommendation) {
        recommendationByReviewer[recommendation.signatures[0]] = recommendation;
      });
      var decisions = submission.details.directReplies.filter(function(reply) {
        return reply.invitations.indexOf(VENUE_ID + '/Paper' + number + '/-/Decision') >= 0;
      });
      var paperReviewers = reviewersByNumber[number] || [];
      var paperActionEditors = aeByNumber[number] || [];
      var paperReviewerStatus = {};
      var confidences = [];
      var completedReviews = reviews.length && (reviews.length == paperReviewers.length);
      var formattedSubmission = {
        id: submission.id,
        forum: submission.forum,
        number: number,
        cdate: submission.cdate,
        mdate: submission.mdate,
        tcdate: submission.tcdate,
        tmdate: submission.tmdate,
        showDates: true,
        content: {
          title: submission.content.title.value,
          authors: submission.content.authors.value,
          authorids: submission.content.authorids.value
        }
      };

      paperReviewers.forEach(function(reviewer) {
        var completedReview = reviews.find(function(review) { return review.signatures[0].endsWith('/Reviewer_' + reviewer.anonId); });
        var status = {};
        if (completedReview) {
          var reviewerRecommendation = recommendationByReviewer[completedReview.signatures[0]];
          status = {};
          if (reviewerRecommendation) {
            status.Recommendation = reviewerRecommendation.content.decision_recommendation.value;
            status.Certifications = reviewerRecommendation.content.certification_recommendations ? reviewerRecommendation.content.certification_recommendations.value.join(', ') : '';
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
          reviewerStatus.reviewerProgressData.papers.push({ note: formattedSubmission, review: completedReview ? { forum: completedReview.forum, status: status } : null});
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

      paperActionEditors.forEach(function(actionEditor, number) {
        var completedDecision = decisions.find(function(decision) { return decision.signatures[0] == VENUE_ID + '/Paper' + number + '/Action_Editors'; });
        var actionEditorStatus = actionEditorStatusById[actionEditor.id];
        if (actionEditorStatus) {
          actionEditorStatus.reviewProgressData.numPapers += 1;
          actionEditorStatus.decisionProgressData.numPapers +=1;
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

      var metaReview = null;
      var decision = decisions.length && decisions[0];
      if (decision) {
        metaReview = { id: decision.id, forum: submission.id, content: { recommendation: decision.content.recommendation.value, certification: (decision.content.certifications && decision.content.certifications.value) || [] }};
      }

      paperStatusRows.push({
        submissionNumber: { number: parseInt(number)},
        submission: formattedSubmission,
        reviewProgressData: {
          noteId: submission.id,
          paperNumber: number,
          numSubmittedReviews: reviews.length,
          numReviewers: paperReviewers.length,
          reviewers: paperReviewerStatus,
          sendReminder: true,
          referrer: referrerUrl,
          actions: ['.TMLR/Under_Review', '.TMLR/Submitted'].includes(submission.content.venueid.value) ? [
            {
              name: 'Edit Assignments',
              url: '/invitation?id=.TMLR/Paper' + number + '/Reviewers/-/Assignment'
            },
            {
              name: 'Edit Review Invitation',
              url: '/invitation/edit?id=.TMLR/Paper' + number + '/-/Review'
            }
          ] : []
        },
        areachairProgressData: {
          recommendation: metaReview && metaReview.content.recommendation,
          status: {
            Certification: metaReview ? metaReview.content.certification.join(', ') : ''
          },
          numMetaReview: metaReview ? 'One' : 'No',
          areachair: { name: paperActionEditors.map(function(ae) { return view.prettyId(ae.id); }), email: paperActionEditors.map(function(ae) { return ae.id; }) },
          metaReview: metaReview,
          referrer: referrerUrl,
          metaReviewName: 'Decision',
          committeeName: 'Action Editor',
          actions: ['.TMLR/Under_Review', '.TMLR/Submitted'].includes(submission.content.venueid.value) ? [
            {
              name: 'Edit Assignments',
              url: '/edges/browse?traverse=.TMLR/Action_Editors/-/Assignment&edit=.TMLR/Action_Editors/-/Assignment&browse=.TMLR/Action_Editors/-/Affinity_Score;.TMLR/Action_Editors/-/Conflict;.TMLR/Action_Editors/-/Custom_Max_Papers,head:ignore&version=2'
            }
          ] : []
        },
        status: submission.content.venue.value,
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
      headings: ['#', 'Paper Summary',
      'Review Progress', 'Action Editor Decision', 'Status'],
      renders: [
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
        Paper_Submission_Date: function(row) { return row.submission.cdate; },
        Number_of_Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
        Number_of_Reviews_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedReviews; },
        Decision: function(row) { return row.areachairProgressData.recommendation; },
        Status: function(row) { return row.status; }
      },
      searchProperties: {
        number: ['submissionNumber.number'],
        id: ['submission.id'],
        title: ['submission.content.title'],
        submissionDate: ['submission.cdate'],
        author: ['submission.content.authors','note.content.authorids'], // multi props
        keywords: ['submission.content.keywords'],
        reviewer: ['reviewProgressData.reviewers'],
        numReviewersAssigned: ['reviewProgressData.numReviewers'],
        numReviewsDone: ['reviewProgressData.numSubmittedReviews'],
        decision: ['areachairProgressData.recommendation'],
        status: ['status'],
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
        $('.console-table th').eq(0).css('width', '5%');
        $('.console-table th').eq(1).css('width', '25%');
        $('.console-table th').eq(2).css('width', '30%');
        $('.console-table th').eq(3).css('width', '28%');
        $('.console-table th').eq(4).css('width', '12%');
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

}

main();
