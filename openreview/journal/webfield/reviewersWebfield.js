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
var HEADER = {
  title: SHORT_PHRASE + ' Reviewer Console',
  instructions: 'Visit the <a href="https://' + WEBSITE + '" target="_blank" rel="nofollow"> ' + SHORT_PHRASE + ' website</a> for the reviewer guidelines.'
};
var REVIEWERS_NAME = '';
var REVIEW_NAME = 'Review';
var ACTION_EDITORS_NAME = '';
var OFFICIAL_RECOMMENDATION_NAME = 'Official_Recommendation';
var DECISION_NAME = 'Decision';
var SUBMISSION_GROUP_NAME = 'Paper';
var REVIEWERS_ID = VENUE_ID + '/' + REVIEWERS_NAME;
var REVIEWERS_CUSTOM_MAX_PAPERS_NAME = 'Custom_Max_Papers';
var REVIEWERS_AVAILABILITY_NAME = 'Assignment_Availability';
var REVIEWERS_EXPERTISE_SELECTION_ID = REVIEWERS_ID + '/-/Expertise_Selection';
var referrerUrl = encodeURIComponent('[Reviewer Console](/group?id=' + VENUE_ID + '/' + REVIEWERS_NAME + '#assigned-papers)');


HEADER.instructions += "<br><br><strong>Expertise Selection:</strong><br><a href=/invitation?id=" + REVIEWERS_EXPERTISE_SELECTION_ID + "&referrer=" + referrerUrl + "> Select your expertise</a>"


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
      Webfield2.api.getAssignedInvitations(VENUE_ID, REVIEWERS_NAME, { numbers: Object.keys(assignedGroups), submissionGroupName: SUBMISSION_GROUP_NAME }),
      Webfield2.api.getAllSubmissions(SUBMISSION_ID, { numbers: Object.keys(assignedGroups), domain: VENUE_ID}),
      Webfield2.api.getAll('/invitations', {
        id: REVIEWERS_ID + '/-/' + REVIEWERS_AVAILABILITY_NAME,
        type: 'edges',
        domain: VENUE_ID
      }).then(function(invitations) {
        return invitations[0];
      }),
      Webfield2.api.getAll('/invitations', {
        id: REVIEWERS_ID + '/-/' + REVIEWERS_CUSTOM_MAX_PAPERS_NAME,
        type: 'edges',
        domain: VENUE_ID
      }).then(function(invitations) {
        return invitations[0];
      }),
      Webfield2.api.getAll('/edges', {
        invitation: REVIEWERS_ID + '/-/' + REVIEWERS_AVAILABILITY_NAME,
        tail: user.profile.id,
        domain: VENUE_ID
      }).then(function(edges) {
        return edges && edges[0];
      }),
      Webfield2.api.getAll('/edges', {
        invitation: REVIEWERS_ID + '/-/' + REVIEWERS_CUSTOM_MAX_PAPERS_NAME,
        tail: user.profile.id,
        domain: VENUE_ID
      }).then(function(edges) {
        return edges && edges[0];
      })
    );
  })
}

var formatData = function(assignedGroups, actionEditorsByNumber, invitations, submissions, availabilityInvitation, customQuotaInvitation, availabilityEdge, customQuotaEdge) {

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
      content: Object.keys(submission.content).reduce(function(content, currentValue) {
        content[currentValue] = submission.content[currentValue].value;
        return content;
      }, {}),
      referrerUrl: referrerUrl
    };
    var assignedReviewers = assignedGroups[number];
    var assignedGroup = assignedReviewers.find(function(group) { return group.id ==  user.profile.id && group.anonId;  });
    var reviewInvitationId = VENUE_ID + '/Paper' + number + '/-/' + REVIEW_NAME;
    var review = assignedGroup ? submission.details.replies.find(function(reply) {
      return reply.invitations.indexOf(reviewInvitationId) >= 0 && reply.signatures[0] == (VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Reviewer_' + assignedGroup.anonId);
    }) : null;
    var recommendations = Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, OFFICIAL_RECOMMENDATION_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var recommendationByReviewer = {};
    recommendations.forEach(function(recommendation) {
      recommendationByReviewer[recommendation.signatures[0]] = recommendation;
    });
    var decisions =  Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, DECISION_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME });
    var decision = decisions.length && decisions[0];
    var reviewInvitation = invitations.find(function(invitation) { return invitation.id == reviewInvitationId; })

    rows.push({
      submissionNumber: { number: number},
      submission: formattedSubmission,
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
  })

  if (availabilityInvitation) {
    availabilityInvitation.details = {
      repliedEdges: availabilityEdge ? [availabilityEdge] : [],
    }
  }

  if (customQuotaInvitation) {
    customQuotaInvitation.details = {
      repliedEdges: customQuotaEdge ? [customQuotaEdge] : [],
    }
  }  


  return venueStatusData = {
    invitations: invitations,
    rows: rows,
    availabilityInvitation: availabilityInvitation,
    customQuotaInvitation: customQuotaInvitation
  };

}

var renderData = function(venueStatusData) {

  if (venueStatusData.availabilityInvitation) {
    Webfield2.ui.renderEdgeWidget('#invitation', venueStatusData.availabilityInvitation, { fieldName: venueStatusData.availabilityInvitation.edge.label ? 'label': 'weight' });  
  }

  if (venueStatusData.customQuotaInvitation) {
    Webfield2.ui.renderEdgeWidget('#invitation', venueStatusData.customQuotaInvitation, { fieldName: venueStatusData.customQuotaInvitation.edge.label ? 'label': 'weight' });  
  }

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
            '<p>' + (data.recommendation.content.decision_recommendation?.value  || 'Yes' )+ '</p>' +
            '<h4>Certifications:</h4>' +
            '<p>' + ((data.recommendation.content.certification_recommendations && data.recommendation.content.certification_recommendations.value.join(', ')) || '') + '</p>';
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
