// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Author Console Webfield
// ------------------------------------

// Constants
var VENUE_ID = '';
var SHORT_PHRASE = '';
var SUBMISSION_ID = '';
var HEADER = {
  title: SHORT_PHRASE + ' Reviewer Console',
  instructions: 'Visit <a href="https://jmlr.org/tmlr" target="_blank" rel="nofollow">jmlr.org/tmlr</a> for the TMLR reviewer guidelines.'
};
var REVIEWERS_NAME = '';
var REVIEW_NAME = 'Review';
var ACTION_EDITORS_NAME = '';


function main() {

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Assigned Papers', 'Reviewer Tasks'],
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

  return Webfield2.api.getGroupsByNumber(VENUE_ID, REVIEWERS_NAME, { assigned: true })
  .then(function(assignedGroups) {
    return $.when(
      assignedGroups,
      Webfield2.api.getGroupsByNumber(VENUE_ID, ACTION_EDITORS_NAME),
      Webfield2.api.getAssignedInvitations(VENUE_ID, REVIEWERS_NAME),
      Webfield2.api.getAllSubmissions(SUBMISSION_ID, { numbers: Object.keys(assignedGroups)})
    );
  })
}

var formatData = function(assignedGroups, actionEditorsByNumber, invitations, submissions) {

  var referrerUrl = encodeURIComponent('[Reviewer Console](/group?id=' + VENUE_ID + '/' + REVIEWERS_NAME + '#assigned-papers)');

  var submissionsByNumber = _.keyBy(submissions, 'number');

  //build the rows
  var rows = [];

  Object.keys(assignedGroups).forEach(function(number) {
    var submission = submissionsByNumber[number];
    if (submission) {

      var assignedReviewers = assignedGroups[number];
      var assignedGroup = assignedReviewers.find(function(group) { return group.id ==  user.profile.id && group.anonId;  });
      var reviewInvitationId = VENUE_ID + '/Paper' + number + '/-/' + REVIEW_NAME;
      var review = assignedGroup ? submission.details.directReplies.find(function(reply) {
        return reply.invitations.indexOf(reviewInvitationId) >= 0 && reply.signatures[0] == (VENUE_ID + '/Paper' + number + '/Reviewer_' + assignedGroup.anonId);
      }) : null;
      var recommendations = submission.details.directReplies.filter(function(reply) {
        return reply.invitations.indexOf(VENUE_ID + '/Paper' + submission.number + '/-/Official_Recommendation') >= 0;
      });
      var recommendationByReviewer = {};
      recommendations.forEach(function(recommendation) {
        recommendationByReviewer[recommendation.signatures[0]] = recommendation;
      });
      var decision = submission.details.directReplies.find(function(reply) {
        return reply.invitations.indexOf(VENUE_ID + '/Paper' + number + '/-/Decision') >= 0;
      });
      var reviewInvitation = invitations.find(function(invitation) { return invitation.id == reviewInvitationId; })

      rows.push({
        submissionNumber: { number: number},
        submission: { number: number, forum: submission.forum, content: { title: submission.content.title.value, authors: ['Anonymous']}, referrer: referrerUrl},
        reviewStatus: {
          invitationUrl: reviewInvitation && '/forum?id=' + submission.forum + '&noteId=' + submission.forum + '&invitationId=' + reviewInvitation.id + '&referrer=' + referrerUrl,
          review: review,
          recommendation: review ? recommendationByReviewer[review.signatures[0]] : null,
          editUrl: review && ('/forum?id=' + submission.forum + '&noteId=' + review.id + '&referrer=' + referrerUrl)
        },
        actionEditorData: {
          recommendation: decision && decision.content.recommendation.value,
          url: decision ? ('/forum?id=' + submission.id + '&noteId=' + decision.id + '&referrer=' + referrerUrl) : null
        }
      })
    }
  })


  return venueStatusData = {
    invitations: invitations,
    rows: rows
  };

}

var renderData = function(venueStatusData) {

  Webfield2.ui.renderTasks('#reviewer-tasks', venueStatusData.invitations, { referrer: encodeURIComponent('[Reviewer Console](/group?id=' + VENUE_ID + '/' + REVIEWERS_NAME + '#reviewer-tasks)') + '&t=' + Date.now()});

  Webfield2.ui.renderTable('#assigned-papers', venueStatusData.rows, {
    headings: ['#', 'Paper Summary', 'Your Review', 'Decision Status'],
    renders: [
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      Handlebars.templates.noteSummary,
      function(data) {
        if (data.review) {
          var recommendationHtml = '';
          if (data.recommendation) {
            recommendationHtml = '<h4>Recommendation:</h4>' +
            '<p>' + data.recommendation.content.decision_recommendation.value + '</p>' +
            '<h4>Certifications:</h4>' +
            '<p>' + (data.recommendation.content.certification_recommendations && data.recommendation.content.certification_recommendations.value.join(', ')) + '</p>';
          }
          return '<div>' +
          recommendationHtml +
          '<p>' +
            '<a href="' + data.editUrl + '" target="_blank">Read ' + REVIEW_NAME+ '</a>' +
          '</p>' +
          '</div>';
        } else if (data.invitationUrl) {
          return '<h4><a href="' + data.invitationUrl + '" target="_blank">Submit ' + REVIEW_NAME + '</a></h4>'
        }
        return '<div></div>'
      },
      function(data) {
        if (data.recommendation) {
          return '<div>' +
          '<h4>Action Editor Decision:</h4>' +
          '<p>' +
            '<strong>' + data.recommendation + '</strong>' +
          '</p>' +
          '<p>' +
            '<a href="' + data.url + '" target="_blank">Read</a>' +
          '</p>' +
          '</div>'
        }
        return '<div><h4><strong>No Recommendation</strong></h4></div>'
      }
    ],
    extraClasses: 'console-table'
  })

}


// Go!
main();
