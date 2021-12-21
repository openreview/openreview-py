// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var VENUE_ID = '';
var SHORT_PHRASE = '';
var SUBMISSION_ID = '';
var ACTION_EDITOR_NAME = '';
var REVIEWERS_NAME = '';
var ACTION_EDITOR_ID = VENUE_ID + '/' + ACTION_EDITOR_NAME;
var REVIEW_NAME = 'Review';
var OFFICIAL_RECOMMENDATION_NAME = 'Official_Recommendation';
var SUBMISSION_GROUP_NAME = 'Paper';
var DECISION_NAME = 'Decision';
var UNDER_REVIEW_STATUS = VENUE_ID + '/Under_Review';

var REVIEWERS_ID = VENUE_ID + '/' + REVIEWERS_NAME;
var REVIEWERS_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Assignment';
var REVIEWERS_CONFLICT_ID = REVIEWERS_ID + '/-/Conflict';
var REVIEWERS_AFFINITY_SCORE_ID = REVIEWERS_ID + '/-/Affinity_Score';
var REVIEWERS_CUSTOM_MAX_PAPERS_ID = REVIEWERS_ID + '/-/Custom_Max_Papers';
var REVIEWERS_PENDING_REVIEWS_ID = REVIEWERS_ID + '/-/Pending_Reviews';
var ACTION_EDITORS_ASSIGNMENT_ID = ACTION_EDITOR_ID + '/-/Assignment';

var reviewers_url = '/edges/browse?start=' + ACTION_EDITORS_ASSIGNMENT_ID + ',tail=' + user.profile.id +
'&traverse=' + REVIEWERS_ASSIGNMENT_ID +
'&edit=' + REVIEWERS_ASSIGNMENT_ID +
'&browse=' + REVIEWERS_AFFINITY_SCORE_ID + ';' + REVIEWERS_CONFLICT_ID + ';' + REVIEWERS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' + REVIEWERS_PENDING_REVIEWS_ID + ',head:ignore' +
'&maxColumns=2&version=2&referrer=[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + ')';


var HEADER = {
  title: SHORT_PHRASE + ' Action Editor Console',
  instructions: "<strong>Edge Browser:</strong><br><a href='" + reviewers_url + "'> Modify Reviewer Assignments</a> </p>"
};

// Main function is the entry point to the webfield code
var main = function() {

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Assigned Papers', 'Action Editor Tasks'],
    referrer: args && args.referrer
  })

  loadData()
  .then(formatData)
  .then(renderData)
  .then(Webfield2.ui.done)
  .fail(Webfield2.ui.errorMessage);
};


var loadData = function() {

  return Webfield2.api.getGroupsByNumber(VENUE_ID, ACTION_EDITOR_NAME, { assigned: true })
  .then(function(assignedGroups) {
    return $.when(
      Webfield2.api.getGroupsByNumber(VENUE_ID, REVIEWERS_NAME),
      Webfield2.api.getAssignedInvitations(VENUE_ID, ACTION_EDITOR_NAME),
      Webfield2.api.getAllSubmissions(SUBMISSION_ID, { numbers: Object.keys(assignedGroups) }),
      Webfield2.api.get('/edges', { invitation: REVIEWERS_ASSIGNMENT_ID, groupBy: 'head'})
      .then(function(result) { return result.groupedEdges; })
    );
  })

}

var formatData = function(reviewersByNumber, invitations, submissions, assignmentEdges) {
  var referrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + '#assigned-papers)');

    //build the rows
  var rows = [];

  submissions.forEach(function(submission) {

    var number = submission.number;
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
    var reviews = Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, REVIEW_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var recommendations = Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, OFFICIAL_RECOMMENDATION_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var recommendationByReviewer = {};
    recommendations.forEach(function(recommendation) {
      recommendationByReviewer[recommendation.signatures[0]] = recommendation;
    });
    var decisions = Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, DECISION_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var decision = decisions.length && decisions[0];
    var reviewers = reviewersByNumber[number] || [];
    var reviewerStatus = {};

    reviewers.forEach(function(reviewer) {
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
      reviewerStatus[reviewer.anonId] = {
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
          invitationId: Webfield2.utils.getInvitationId(VENUE_ID, submission.number, REVIEW_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME })
        })
      }
    })

    rows.push({
      submissionNumber: { number: parseInt(number)},
      submission: formattedSubmission,
      reviewProgressData: {
        noteId: submission.id,
        paperNumber: number,
        numSubmittedReviews: reviews.length,
        numReviewers: reviewers.length,
        reviewers: reviewerStatus,
        sendReminder: true,
        referrer: referrerUrl,
        actions: submission.content.venueid.value == UNDER_REVIEW_STATUS ? [
          {
            name: 'Edit Assignments',
            url: '/edges/browse?start=staticList,type:head,ids:' + submission.id + '&traverse=' + REVIEWERS_ASSIGNMENT_ID +
            '&edit=' + REVIEWERS_ASSIGNMENT_ID +
            '&browse=' + REVIEWERS_AFFINITY_SCORE_ID + ';' + REVIEWERS_CONFLICT_ID + ';' + REVIEWERS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' + REVIEWERS_PENDING_REVIEWS_ID + ',head:ignore&' +
            'maxColumns=2&version=2'
          }
        ] : []
      },
      actionEditorData: {
        committeeName: 'Action Editor',
        recommendation: decision && decision.content.recommendation.value,
        editUrl: decision ? ('/forum?id=' + submission.id + '&noteId=' + decision.id + '&referrer=' + referrerUrl) : null
      },
      status: submission.content.venue.value
    })

    //Add the assignment edges to each paper assignmnt invitation
    paper_assignment_invitation = invitations.find(function(i) { return i.id == Webfield2.utils.getInvitationId(VENUE_ID, submission.number, 'Assignment', { prefix: REVIEWERS_NAME, submissionGroupName: SUBMISSION_GROUP_NAME })});
    if (paper_assignment_invitation) {
      var foundEdges = assignmentEdges.find(function(a) { return a.id.head == submission.id})
      if (foundEdges) {
        paper_assignment_invitation.details.repliedEdges = foundEdges.values;
      }
    }
  })


  return venueStatusData = {
    invitations: invitations,
    rows: rows
  };
}

// Render functions
var renderData = function(venueStatusData) {

  Webfield2.ui.renderTasks('#action-editor-tasks', venueStatusData.invitations, { referrer: encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + '#action-editor-tasks)')});

  Webfield2.ui.renderTable('#assigned-papers', venueStatusData.rows, {
      headings: ['#', 'Paper Summary',
      'Review Progress', 'Decision Status', 'Status'],
      renders: [
        function(data) {
          return '<strong class="note-number">' + data.number + '</strong>';
        },
        Handlebars.templates.noteSummary,
        Handlebars.templates.noteReviewers,
        Handlebars.templates.noteMetaReviewStatus,
        function(data) {
          return '<h4>' + data + '</h4>';
        }
      ],
      sortOptions: {
        Paper_Number: function(row) { return row.submissionNumber.number; },
        Paper_Title: function(row) { return _.toLower(_.trim(row.submission.content.title)); },
        Number_of_Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
        Number_of_Reviews_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedReviews; },
        Recommendation: function(row) { return row.actionEditorData.recommendation; },
        Status: function(row) { return row.status; }
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
        recommendation: ['actionEditorData.recommendation'],
        status: ['status']
      },
      reminderOptions: {
        container: 'a.send-reminder-link',
        defaultSubject: SHORT_PHRASE + ' Reminder',
        defaultBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the review page:\n\n{{submit_review_link}}' +
        '\n\nThank you,\n' + SHORT_PHRASE + ' Action Editor'
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
}

main();
