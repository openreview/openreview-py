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
var JOURNAL_REQUEST_ID = '';
var REVIEWER_REPORT_ID = '';
var NUMBER_OF_REVIEWERS = 3;
var PREFERRED_EMAILS_ID = '';

var REVIEWERS_ID = VENUE_ID + '/' + REVIEWERS_NAME;
var REVIEWERS_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Assignment';
var REVIEWERS_INVITE_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Invite_Assignment';
var REVIEWERS_CONFLICT_ID = REVIEWERS_ID + '/-/Conflict';
var REVIEWERS_AFFINITY_SCORE_ID = REVIEWERS_ID + '/-/Affinity_Score';
var REVIEWERS_CUSTOM_MAX_PAPERS_ID = REVIEWERS_ID + '/-/Custom_Max_Papers';
var REVIEWERS_PENDING_REVIEWS_ID = REVIEWERS_ID + '/-/Pending_Reviews';
var ACTION_EDITORS_ASSIGNMENT_ID = ACTION_EDITOR_ID + '/-/Assignment';
var ACTION_EDITORS_EXPERTISE_SELECTION_ID = ACTION_EDITOR_ID + '/-/Expertise_Selection';
var CUSTOM_MAX_PAPERS_NAME = 'Custom_Max_Papers';
var AVAILABILITY_NAME = 'Assignment_Availability';
var REVIEWERS_AVAILABILITY_ID = REVIEWERS_ID + '/-/' + AVAILABILITY_NAME;
var REVIEWERS_REPORT_ID = REVIEWERS_ID + '/-/Reviewer_Report';


var SUBMISSION_GROUP_NAME = 'Paper';
var RECOMMENDATION_NAME = 'Recommendation';
var REVIEW_APPROVAL_NAME = 'Review_Approval';
var DESK_REJECTION_APPROVAL_NAME = 'Desk_Rejection_Approval';
var REVIEW_NAME = 'Review';
var OFFICIAL_RECOMMENDATION_NAME = 'Official_Recommendation';
var DECISION_NAME = 'Decision';
var DECISION_APPROVAL_NAME = 'Decision_Approval';
var CAMERA_READY_REVISION_NAME = 'Camera_Ready_Revision';
var CAMERA_READY_VERIFICATION_NAME = 'Camera_Ready_Verification';
var UNDER_REVIEW_STATUS = VENUE_ID + '/Under_Review';
var SUBMITTED_STATUS = VENUE_ID + '/Submitted';
var ASSIGNMENT_ACKNOWLEDGEMENT_NAME = 'Assignment/Acknowledgement';

var referrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + ')');
var reviewersUrl = '/edges/browse?start=' + ACTION_EDITORS_ASSIGNMENT_ID + ',tail:' + user.profile.id +
  '&traverse=' + REVIEWERS_ASSIGNMENT_ID +
  '&edit=' + REVIEWERS_ASSIGNMENT_ID + ';' +
    REVIEWERS_INVITE_ASSIGNMENT_ID + 
  '&browse=' + REVIEWERS_AFFINITY_SCORE_ID + ';' + 
    REVIEWERS_CONFLICT_ID + ';' + 
    REVIEWERS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' +
    REVIEWERS_PENDING_REVIEWS_ID + ',head:ignore;' +
    REVIEWERS_AVAILABILITY_ID + ',head:ignore' +
  '&maxColumns=2&version=2' +
  '&filter=' + REVIEWERS_PENDING_REVIEWS_ID + ' == 0 AND ' + REVIEWERS_AVAILABILITY_ID + ' == Available AND ' + REVIEWERS_CONFLICT_ID + ' == 0' +
  "&preferredEmailInvitationId=" + PREFERRED_EMAILS_ID +
  '&referrer=' + referrerUrl;


var HEADER = {
  title: SHORT_PHRASE + ' Action Editor Console',
  instructions: "<strong>Reviewer Assignment Browser:</strong><br><a href='" + reviewersUrl + "'> Modify Reviewer Assignments</a>"
};

if (JOURNAL_REQUEST_ID) {
  HEADER.instructions += "<br><br><strong>Journal Recruitment:</strong><br><a href=/forum?id=" + JOURNAL_REQUEST_ID + "&referrer=" + referrerUrl + "> Recruit Reviewer</a>"
}

if (REVIEWER_REPORT_ID) {
  HEADER.instructions += "<br><br><strong>Reviewer Report:</strong><br><a href=/forum?id=" + REVIEWER_REPORT_ID + "&referrer=" + referrerUrl + "> Report Reviewer</a>"
}

HEADER.instructions += "<br><br><strong>Expertise Selection:</strong><br><a href=/invitation?id=" + ACTION_EDITORS_EXPERTISE_SELECTION_ID + "&referrer=" + referrerUrl + "> Select your expertise</a>"


// Helpers
var getInvitationId = function(number, name, prefix) {
  return Webfield2.utils.getInvitationId(VENUE_ID, number, name, { prefix: prefix, submissionGroupName: SUBMISSION_GROUP_NAME })
};

var getReplies = function(submission, name, prefix) {
  return Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, name, { prefix: prefix, submissionGroupName: SUBMISSION_GROUP_NAME });
};

var getRatingInvitations = function(invitationsById, number) {
  var invitations = [];
  Object.keys(invitationsById).forEach(function(invitationId) {
    if (invitationId.match(VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '.*/-/Rating')) {
      invitations.push(invitationsById[invitationId]);
    }
  })
  return invitations;
}

var getRatingReplies = function(submission, ratingInvitations) {
  var replies = [];
  ratingInvitations.forEach(function(invitation) {
    var ratingReplies = submission.details.replies.filter(function(reply) {
      return reply.invitations.includes(invitation.id);
    });
    replies = replies.concat(ratingReplies);
  })
  return replies;
}


// Main function is the entry point to the webfield code
var main = function() {
  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Assigned Papers', 'Action Editor Tasks'],
    referrer: args && args.referrer
  });

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
        Webfield2.api.getGroupsByNumber(VENUE_ID, REVIEWERS_NAME, { withProfiles: true }),
        Webfield2.api.getAssignedInvitations(VENUE_ID, ACTION_EDITOR_NAME, { numbers: Object.keys(assignedGroups), submissionGroupName: SUBMISSION_GROUP_NAME }),
        Webfield2.api.getAllSubmissions(SUBMISSION_ID, { numbers: Object.keys(assignedGroups), domain: VENUE_ID }),
        Webfield2.api.getAll('/invitations', {
          prefix: VENUE_ID + '/' + SUBMISSION_GROUP_NAME,
          type: 'all',
          select: 'id,cdate,duedate,expdate',
          sort: 'cdate:asc',
          // expired: true,
          domain: VENUE_ID
        }).then(function(invitations) {
          return _.keyBy(invitations, 'id');
        }),
        Webfield2.api.getAll('/invitations', {
          id: ACTION_EDITOR_ID + '/-/' + AVAILABILITY_NAME,
          type: 'edges',
          domain: VENUE_ID
        }).then(function(invitations) {
          return invitations[0];
        }),
        Webfield2.api.getAll('/invitations', {
          id: ACTION_EDITOR_ID + '/-/' + CUSTOM_MAX_PAPERS_NAME,
          type: 'edges',
          domain: VENUE_ID
        }).then(function(invitations) {
          return invitations[0];
        }),
        Webfield2.api.getAll('/edges', {
          invitation: ACTION_EDITOR_ID + '/-/' + AVAILABILITY_NAME,
          tail: user.profile.id,
          domain: VENUE_ID
        }).then(function(edges) {
          return edges && edges[0];
        }),
        Webfield2.api.getAll('/edges', {
          invitation: ACTION_EDITOR_ID + '/-/' + CUSTOM_MAX_PAPERS_NAME,
          tail: user.profile.id,
          domain: VENUE_ID
        }).then(function(edges) {
          return edges && edges[0];
        })
      );
    });
};

var formatData = function(reviewersByNumber, invitations, submissions, invitationsById, availabilityInvitation, customQuotaInvitation, availabilityEdge, customQuotaEdge) {
  var referrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + '#assigned-papers)');

  // build the rows
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

    // Build array of tasks
    var tasks = [];
    // Review approval by AE
    var reviewApprovalInvitation = invitationsById[getInvitationId(number, REVIEW_APPROVAL_NAME)];
    var reviewApprovalNotes = getReplies(submission, REVIEW_APPROVAL_NAME);
    // Desk Rejection approval by EIC
    var deskRejectionApprovalInvitation = invitationsById[getInvitationId(number, DESK_REJECTION_APPROVAL_NAME)];
    var deskRejectionApprovalNotes = getReplies(submission, DESK_REJECTION_APPROVAL_NAME);
    // Reviewer assignment by AE
    var reviewerAssignmentInvitation = invitationsById[getInvitationId(number, 'Assignment', REVIEWERS_NAME)];
    // Reviews by Reviewers
    var reviewInvitation = invitationsById[getInvitationId(number, REVIEW_NAME)];
    var reviewNotes = getReplies(submission, REVIEW_NAME);
    // Official Recommendations by Reviewers
    var officialRecommendationInvitation = invitationsById[getInvitationId(number, OFFICIAL_RECOMMENDATION_NAME)];
    var officialRecommendationNotes = getReplies(submission, OFFICIAL_RECOMMENDATION_NAME);
    // Reviewer Rating by AE
    var reviewerRatingInvitations = getRatingInvitations(invitationsById, number);
    var reviewerRatingReplies = getRatingReplies(submission, reviewerRatingInvitations);
    // Decision by AE
    var decisionInvitation = invitationsById[getInvitationId(number, DECISION_NAME)];
    var decisionNotes = getReplies(submission, DECISION_NAME);
    // Decision Approval by EIC
    var decisionApprovalInvitation = invitationsById[getInvitationId(number, DECISION_APPROVAL_NAME)];
    var decisionApprovalNotes = getReplies(submission, DECISION_APPROVAL_NAME);
    // Camera Ready Revision by Authors
    var cameraReadyRevisionInvitation = invitationsById[getInvitationId(number, CAMERA_READY_REVISION_NAME)];
    // Camera Ready Verification by AE
    var cameraReadyVerificationInvitation = invitationsById[getInvitationId(number, CAMERA_READY_VERIFICATION_NAME)];
    var cameraReadyVerificationNotes = getReplies(submission, CAMERA_READY_VERIFICATION_NAME);

    if (reviewApprovalInvitation) {
      tasks.push({
        id: reviewApprovalInvitation.id,
        cdate: reviewApprovalInvitation.cdate,
        duedate: reviewApprovalInvitation.duedate,
        complete: reviewApprovalNotes.length > 0,
        replies: reviewApprovalNotes
      });
    }

    if (deskRejectionApprovalInvitation) {
      var task = {
        id: deskRejectionApprovalInvitation.id,
        cdate: deskRejectionApprovalInvitation.cdate,
        duedate: deskRejectionApprovalInvitation.duedate,
        complete: deskRejectionApprovalNotes.length > 0,
        replies: deskRejectionApprovalNotes
      };
      tasks.push(task);
    }    

    if (reviewerAssignmentInvitation) {
      tasks.push({
        id: reviewerAssignmentInvitation.id,
        cdate: reviewerAssignmentInvitation.cdate,
        duedate: reviewerAssignmentInvitation.duedate,
        complete: reviewers.length >= NUMBER_OF_REVIEWERS,
        replies: reviewers
      });
    }

    if (reviewInvitation) {
      tasks.push({
        id: reviewInvitation.id,
        cdate: reviewInvitation.cdate,
        duedate: reviewInvitation.duedate,
        complete: reviewNotes.length >= NUMBER_OF_REVIEWERS,
        replies: reviewNotes
      });
    }

    if (officialRecommendationInvitation) {
      tasks.push({
        id: officialRecommendationInvitation.id,
        cdate: officialRecommendationInvitation.cdate,
        duedate: officialRecommendationInvitation.duedate,
        complete: officialRecommendationNotes.length >= NUMBER_OF_REVIEWERS,
        replies: officialRecommendationNotes
      });
    }

    if (reviewerRatingInvitations.length) {
      tasks.push({
        id: getInvitationId(number, 'Reviewer_Rating'),
        cdate: reviewerRatingInvitations[0].cdate,
        duedate: reviewerRatingInvitations[0].duedate,
        complete: reviewerRatingReplies.length == reviewNotes.length,
        replies: reviewerRatingReplies
      });
    }

    if (decisionInvitation) {
      tasks.push({
        id: decisionInvitation.id,
        cdate: decisionInvitation.cdate,
        duedate: decisionInvitation.duedate,
        complete: decisionNotes.length > 0,
        replies: decisionNotes
      });
    }

    if (decisionApprovalInvitation) {
      tasks.push({
        id: decisionApprovalInvitation.id,
        cdate: decisionApprovalInvitation.cdate,
        duedate: decisionApprovalInvitation.duedate,
        complete: decisionApprovalNotes.length > 0,
        replies: decisionApprovalNotes
      });
    }

    if (cameraReadyRevisionInvitation) {
      tasks.push({
        id: cameraReadyRevisionInvitation.id,
        cdate: cameraReadyRevisionInvitation.cdate,
        duedate: cameraReadyRevisionInvitation.duedate,
        complete: submission.invitations.includes(cameraReadyRevisionInvitation.id),
        replies: []
      });
    }

    if (cameraReadyVerificationInvitation) {
      tasks.push({
        id: cameraReadyVerificationInvitation.id,
        cdate: cameraReadyVerificationInvitation.cdate,
        duedate: cameraReadyVerificationInvitation.duedate,
        complete: cameraReadyVerificationNotes.length > 0,
        replies: cameraReadyVerificationNotes
      });
    }


    reviewers.forEach(function(reviewer) {
      var completedReview = reviews.find(function(review) { return review.signatures[0].endsWith('/Reviewer_' + reviewer.anonId); });
      var assignmentAcknowledgement = getReplies(submission, reviewer.id + '/' + ASSIGNMENT_ACKNOWLEDGEMENT_NAME, REVIEWERS_NAME);
      var status = {
        'profileID': reviewer.id
      };
      var links = {
        'Report': '/forum?id=' + REVIEWER_REPORT_ID + '&noteId=' + REVIEWER_REPORT_ID + '&invitationId=' + REVIEWERS_REPORT_ID + '&edit.note.content.reviewer_id=' + reviewer.id + '&referrer=' + referrerUrl,
      }

      if (assignmentAcknowledgement && assignmentAcknowledgement.length) {
        status.Acknowledged = 'Yes';
      }

      if (completedReview) {
        var reviewerRecommendation = recommendationByReviewer[completedReview.signatures[0]];
        if (reviewerRecommendation) {
          status.Recommendation = reviewerRecommendation.content.decision_recommendation?.value || 'Yes';
          status.Certifications = reviewerRecommendation.content.certification_recommendations ? reviewerRecommendation.content.certification_recommendations.value.join(', ') : '';
        }
        var reviewerRating = submission.details.replies.find(function (p) {
          return p.replyto === completedReview.id && p.invitations.includes(VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Reviewer_' + reviewer.anonId + '/-/Rating');
        });
        if(reviewerRating){
          status.Rating = reviewerRating.content.rating.value;
        }
      }
      reviewerStatus[reviewer.anonId] = {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
        completedReview: completedReview && true,
        completedRecommendation: status.Recommendation && true,
        hasRecommendationStarted: officialRecommendationInvitation && officialRecommendationInvitation.cdate < Date.now(),
        forum: submission.id,
        note: completedReview && completedReview.id,
        status: status,
        links: links,
        forumUrl: 'https://openreview.net/forum?' + $.param({
          id: submission.id,
          noteId: submission.id,
          invitationId: Webfield2.utils.getInvitationId(VENUE_ID, submission.number, REVIEW_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME })
        }),
        paperNumber: number,
        anonymousGroupId: reviewer.anonymousGroupId
      };
    });

    rows.push({
      checked: { noteId: submission.id, checked: false },
      submissionNumber: { number: parseInt(number)},
      submission: formattedSubmission,
      reviewProgressData: {
        noteId: submission.id,
        paperNumber: number,
        numSubmittedReviews: reviews.length,
        numSubmittedRecommendations: recommendations.length,
        numReviewers: reviewers.length,
        reviewers: reviewerStatus,
        expandReviewerList: true,
        sendReminder: true,
        showPreferredEmail: PREFERRED_EMAILS_ID,
        referrer: referrerUrl,
        actions: (submission.content.venueid.value == UNDER_REVIEW_STATUS && reviewerAssignmentInvitation) ? [
          {
            name: 'Edit Assignments',
            url: '/edges/browse?start=staticList,type:head,ids:' + submission.id + '&traverse=' + REVIEWERS_ASSIGNMENT_ID +
            '&edit=' + REVIEWERS_ASSIGNMENT_ID + ';' + REVIEWERS_INVITE_ASSIGNMENT_ID +
            '&browse=' + REVIEWERS_AFFINITY_SCORE_ID + ';' + REVIEWERS_CONFLICT_ID + ';' + REVIEWERS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' + REVIEWERS_PENDING_REVIEWS_ID + ',head:ignore;' + REVIEWERS_AVAILABILITY_ID + ',head:ignore' +
            '&maxColumns=2&version=2' +
            '&filter=' + REVIEWERS_PENDING_REVIEWS_ID + ' == 0 AND ' + REVIEWERS_AVAILABILITY_ID + ' == Available AND ' + REVIEWERS_CONFLICT_ID + ' == 0' +
            "&preferredEmailInvitationId=" + PREFERRED_EMAILS_ID
          }
        ] : [],
        duedate: reviewInvitation && reviewInvitation.duedate || 0
      },
      actionEditorData: {
        committeeName: 'Action Editor',
        recommendation: decision && decision.content.recommendation.value,
        editUrl: decision ? ('/forum?id=' + submission.id + '&noteId=' + decision.id + '&referrer=' + referrerUrl) : null
      },
      tasks: { invitations: tasks, forumId: submission.id },
      status: submission.content.venue?.value
    });

  });

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
};

// Render functions
var renderData = function(venueStatusData) {

  if (venueStatusData.availabilityInvitation) {
    Webfield2.ui.renderEdgeWidget('#invitation', venueStatusData.availabilityInvitation, { fieldName: venueStatusData.availabilityInvitation.edge.label ? 'label': 'weight' });  
  }

  if (venueStatusData.customQuotaInvitation) {
    Webfield2.ui.renderEdgeWidget('#invitation', venueStatusData.customQuotaInvitation, { fieldName: venueStatusData.customQuotaInvitation.edge.label ? 'label': 'weight' });  
  }

  // Assigned Papers Tab
  Webfield2.ui.renderTable('#assigned-papers', venueStatusData.rows, {
    headings: ['<input type="checkbox" class="select-all-papers">', '#', 'Paper Summary', 'Review Progress', 'Decision Status', 'Tasks', 'Status'],
    renders: [
      function(data) {
        return '<label><input type="checkbox" class="select-note-reviewers" data-note-id="' +
          data.noteId + '" ' + (data.checked ? 'checked="checked"' : '') + '></label>';
      },
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      Handlebars.templates.noteSummary,
      Handlebars.templates.noteReviewers,
      Handlebars.templates.noteMetaReviewStatus,
      function(data) {
        return Webfield2.ui.eicTaskList(data.invitations, data.forumId, {
          referrer: encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + ')')
        });
      },
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
      Status: function(row) { return row.status; },
      Review_Due_Date: function(row) { return row.reviewProgressData.duedate; }
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
      status: ['status'],
      default: ['submissionNumber.number', 'submission.content.title']
    },
    reminderOptions: {
      container: 'a.send-reminder-link',
      defaultSubject: SHORT_PHRASE + ' Reminder',
      defaultBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the review page:\n\n{{forumUrl}}' +
        '\n\nThank you,\n' + SHORT_PHRASE + ' Action Editor',
      replyTo: user && user.id,
      messageInvitationId: VENUE_ID + '/Paper{number}/-/Message',
      messageSignature: user && user.profile.id,
      menu: [{
        id: 'all-reviewers',
        name: 'All reviewers of selected papers',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return venueStatusData.rows.map(function(row) {
            return {
              groups: selectedIds.includes(row.submission.id)
                ? Object.values(row.reviewProgressData.reviewers)
                : [],
              forumUrl: 'https://openreview.net/forum?' + $.param({
                id: row.submission.forum
              }),
              number: row.submission.number
            }
          });
        }
      }, {
        id: 'unsubmitted-reviews',
        name: 'Reviewers with missing reviews',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return venueStatusData.rows.map(function(row) {
            return {
              groups: selectedIds.includes(row.submission.id)
                ? Object.values(row.reviewProgressData.reviewers).filter(function(r) {
                    return row.submission.content.venueid === UNDER_REVIEW_STATUS && !r.completedReview;
                  })
                : [],
              forumUrl: 'https://openreview.net/forum?' + $.param({
                id: row.submission.forum,
                noteId: row.submission.forum,
                invitationId: Webfield2.utils.getInvitationId(VENUE_ID, row.submission.number, REVIEW_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME })
              }),
              number: row.submission.number
            }
          });
        }
      }, {
        id: 'unsubmitted-recommendations',
        name: 'Reviewers with missing official recommendations',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return venueStatusData.rows.map(function(row) {
            return {
              groups: selectedIds.includes(row.submission.id)
                ? Object.values(row.reviewProgressData.reviewers).filter(function(r) {
                    return row.submission.content.venueid === UNDER_REVIEW_STATUS && r.hasRecommendationStarted && !r.completedRecommendation;
                  })
                : [],
              forumUrl: 'https://openreview.net/forum?' + $.param({
                id: row.submission.forum,
                noteId: row.submission.forum,
                invitationId: Webfield2.utils.getInvitationId(VENUE_ID, row.submission.number, OFFICIAL_RECOMMENDATION_NAME, { submissionGroupName: SUBMISSION_GROUP_NAME })
              }),
              number: row.submission.number
            }
          });
        }
      }]
    },
    extraClasses: 'console-table paper-table',
    postRenderTable: function() {
      $('.console-table th').eq(0).css('width', '2%');  // [ ]
      $('.console-table th').eq(1).css('width', '3%');  // #
      $('.console-table th').eq(2).css('width', '20%'); // Paper Summary
      $('.console-table th').eq(3).css('width', '22%'); // Review Progress
      $('.console-table th').eq(4).css('width', '22%'); // Action Editor Decision
      $('.console-table th').eq(5).css('width', '20%'); // Tasks
      $('.console-table th').eq(6).css('width', '11%'); // Status
    },
    preferredEmailsInvitationId: PREFERRED_EMAILS_ID
  });

  // Action Editor Tasks Tab
  Webfield2.ui.renderTasks('#action-editor-tasks', venueStatusData.invitations, {
    referrer: encodeURIComponent('[Action Editor Console](/group?id=' + ACTION_EDITOR_ID + '#action-editor-tasks)')
  });
};

main();
