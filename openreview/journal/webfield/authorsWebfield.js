// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Author Console Webfield
// ------------------------------------

// Constants

var VENUE_ID = '';
var SHORT_PHRASE = '';
var WEBSITE = '';
var SUBMISSION_ID = '';
var SUBMISSION_GROUP_NAME = 'Paper';

var HEADER = {
  title: SHORT_PHRASE + ' Author Console',
  instructions: 'Visit the <a href="https://' + WEBSITE + '" target="_blank" rel="nofollow"> ' + SHORT_PHRASE + ' website</a> for the author guidelines.'
};
var AUTHOR_NAME = 'Authors';
var ACTION_EDITORS_NAME = 'Action_Editors';
var REVIEW_NAME = 'Review';
var OFFICIAL_RECOMMENDATION_NAME = 'Official_Recommendation';
var DECISION_NAME = 'Decision';
var AE_RECOMMENDATION_ID = VENUE_ID + '/' + ACTION_EDITORS_NAME + '/-/Recommendation';

function main() {

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Your Submissions', 'Author Tasks'],
    referrer: args && args.referrer
  })

  loadData()
  .then(formatData)
  .then(renderData)
  .then(Webfield2.ui.done)
  .fail(Webfield2.ui.errorMessage);
}

// Load makes all the API calls needed to get the data to render the page
var loadData = function() {
  var notesP = Webfield2.getAll('/notes', {
    'content.authorids': user.profile.id,
    invitation: SUBMISSION_ID,
    details: 'replies',
    sort: 'number:asc',
    domain: VENUE_ID
  });

  return $.when(
    notesP,
    Webfield2.api.getAssignedInvitations(VENUE_ID, AUTHOR_NAME),
    Webfield2.api.get('/edges', { invitation: AE_RECOMMENDATION_ID, groupBy: 'head', domain: VENUE_ID})
    .then(function(result) { return result.groupedEdges; })
  );
}

var formatData = function(notes, invitations, recommendationEdges) {

  var referrerUrl = encodeURIComponent('[Author Console](/group?id=' + VENUE_ID + '/' + AUTHOR_NAME + '#your-submissions)');

  //build the rows
  var rows = [];

  notes.map(function(submission) {
    var reviews =  Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, REVIEW_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var recommendations =  Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, OFFICIAL_RECOMMENDATION_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var recommendationByReviewer = {};
    recommendations.forEach(function(recommendation) {
      recommendationByReviewer[recommendation.signatures[0]] = recommendation;
    });
    var decisions =  Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, DECISION_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var decision = decisions.length && decisions[0];

    rows.push({
      submissionNumber: { number: submission.number},
      submission: { number: submission.number, forum: submission.forum, content: { title: submission.content.title.value, authors: submission.content.authors.value, authorids: submission.content.authorids.value}, referrer: referrerUrl },
      reviewProgressData: {
        noteId: submission.id,
        paperNumber: submission.number,
        reviews: reviews,
        recommendationByReviewer: recommendationByReviewer,
        referrer: referrerUrl
      },
      actionEditorData: {
        recommendation: decision && decision.content.recommendation.value,
        editUrl: decision ? ('/forum?id=' + submission.id + '&noteId=' + decision.id + '&referrer=' + referrerUrl) : null
      }
    })

    //Add the assignment edges to each paper assignmnt invitation
    paper_recommendation_invitation = invitations.find(function(i) { return i.id == Webfield2.utils.getInvitationId(VENUE_ID, submission.number, 'Recommendation', { prefix: ACTION_EDITORS_NAME, submissionGroupName: SUBMISSION_GROUP_NAME })});
    if (paper_recommendation_invitation) {
      var foundEdges = recommendationEdges.find(function(a) { return a.id.head == submission.id})
      if (foundEdges) {
        paper_recommendation_invitation.details.repliedEdges = foundEdges.values;
      }
    }
  });

  return {
    rows: rows,
    invitations: invitations
  }

}

var renderData = function(venueStatusData) {

  Webfield2.ui.renderTasks('#author-tasks', venueStatusData.invitations, { referrer: encodeURIComponent('[Author Console](/group?id=' + VENUE_ID + '/' + AUTHOR_NAME + '#author-tasks)') + '&t=' + Date.now()});

  Webfield2.ui.renderTable('#your-submissions', venueStatusData.rows, {
    headings: ['#', 'Paper Summary', 'Reviews', 'Decision Status'],
    renders: [
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      Handlebars.templates.noteSummary,
      function(data) {
        var reviews = data.reviews || [];
        var reviewList = reviews.map(function(review) {
          var reviewerRecommendation = data.recommendationByReviewer[review.signatures[0]];
          var recommendationString = reviewerRecommendation ? (' / Recommendation: <a href="/forum?id=' + reviewerRecommendation.forum + '&noteId=' + reviewerRecommendation.id + '&referrer=' + data.referrer + '" target="_blank">Recommendation</a>'): '';
          return '<li style="margin-bottom: .25rem;"><strong>' + view.prettyId(_.last(review.signatures[0].split('/'))) + ':</strong> ' +
            '<a href="/forum?id=' + review.forum + '&noteId=' + review.id + '&referrer=' + data.referrer + '" target="_blank">Review</a>' +
            recommendationString +
            '</li>';
        });
        return '<div class="reviewer-progress">' +
          '<h4>' + reviews.length + ' Reviews Submitted / ' + Object.keys(data.recommendationByReviewer).length + ' Recommendations</h4>' +
          '<ul class="list-unstyled" style="font-size: .75rem">' + reviewList.join('\n') + '</ul>' +
          '</div>';
      },
      Handlebars.templates.noteMetaReviewStatus
    ],
    extraClasses: 'console-table'
  })

}


// Go!
main();
