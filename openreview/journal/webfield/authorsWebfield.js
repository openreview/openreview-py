// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Author Console Webfield
// ------------------------------------

// Constants
var VENUE_ID = '.TMLR';
var SHORT_PHRASE = 'TMLR';
var SUBMISSION_ID = '.TMLR/-/Author_Submission';
var HEADER = {
  title: 'TMLR Author Console',
  instructions: 'Visit <a href="https://jmlr.org/tmlr" target="_blank" rel="nofollow">jmlr.org/tmlr</a> for the TMLR author guidelines.'
};
var AUTHOR_NAME = 'Authors';


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
    details: 'directReplies'
  });

  return $.when(notesP, Webfield2.api.getAssignedInvitations(VENUE_ID, AUTHOR_NAME));
}

var formatData = function(notes, invitations) {

  var referrerUrl = encodeURIComponent('[Author Console](/group?id=' + VENUE_ID + '/' + AUTHOR_NAME + '#your-submissions)');

  //build the rows
  var rows = [];

  notes.map(function(submission) {
    var reviews = submission.details.directReplies.filter(function(reply) {
      return reply.invitations.indexOf(VENUE_ID + '/Paper' + submission.number + '/-/Review') >= 0;
    });
    var recommendations = submission.details.directReplies.filter(function(reply) {
      return reply.invitations.indexOf(VENUE_ID + '/Paper' + submission.number + '/-/Official_Recommendation') >= 0;
    });
    var recommendationByReviewer = {};
    recommendations.forEach(function(recommendation) {
      recommendationByReviewer[recommendation.signatures[0]] = recommendation;
    });
    var decision = submission.details.directReplies.find(function(reply) {
      return reply.invitations.indexOf(VENUE_ID + '/Paper' + submission.number + '/-/Decision') >= 0;
    });

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
