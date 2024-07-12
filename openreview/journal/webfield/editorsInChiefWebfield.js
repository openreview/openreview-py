// webfield_template
// Remove line above if you don't want this page to be overwriten

/* globals $: false */
/* globals view: false */
/* globals Handlebars: false */
/* globals Webfield2: false */

// Constants
var VENUE_ID = '';
var SHORT_PHRASE = '';
var SUBMISSION_ID = '';
var EDITORS_IN_CHIEF_NAME = '';
var EDITORS_IN_CHIEF_EMAIL = '';
var REVIEWERS_NAME = '';
var ACTION_EDITOR_NAME = '';
var JOURNAL_REQUEST_ID = '';
var REVIEWER_REPORT_ID = '';
var NUMBER_OF_REVIEWERS = 3;
var PREFERRED_EMAILS_ID = '';
var REVIEWER_ACKOWNLEDGEMENT_RESPONSIBILITY_ID = '';
var ACTION_EDITOR_ID = VENUE_ID + '/' + ACTION_EDITOR_NAME;
var REVIEWERS_ID = VENUE_ID + '/' + REVIEWERS_NAME;
var EDITORS_IN_CHIEF_ID = VENUE_ID + '/' + EDITORS_IN_CHIEF_NAME;
var RESPONSIBILITY_ACK_NAME = 'Responsibility/Acknowledgement';
var ASSIGNMENT_ACKNOWLEDGEMENT_NAME = 'Assignment/Acknowledgement';
var AVAILABILITY_NAME = 'Assignment_Availability';

var REVIEWERS_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Assignment';
var REVIEWERS_INVITE_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Invite_Assignment';
var REVIEWERS_ARCHIVED_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Archived_Assignment';
var REVIEWERS_CONFLICT_ID = REVIEWERS_ID + '/-/Conflict';
var REVIEWERS_AFFINITY_SCORE_ID = REVIEWERS_ID + '/-/Affinity_Score';
var REVIEWERS_CUSTOM_MAX_PAPERS_ID = REVIEWERS_ID + '/-/Custom_Max_Papers';
var REVIEWERS_PENDING_REVIEWS_ID = REVIEWERS_ID + '/-/Pending_Reviews';
var REVIEWERS_AVAILABILITY_ID = REVIEWERS_ID + '/-/' + AVAILABILITY_NAME;
var ACTION_EDITORS_ASSIGNMENT_ID = ACTION_EDITOR_ID + '/-/Assignment';
var ACTION_EDITORS_ARCHIVED_ASSIGNMENT_ID = ACTION_EDITOR_ID + '/-/Archived_Assignment';
var ACTION_EDITORS_CONFLICT_ID = ACTION_EDITOR_ID + '/-/Conflict';
var ACTION_EDITORS_AFFINITY_SCORE_ID = ACTION_EDITOR_ID + '/-/Affinity_Score';
var ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID = ACTION_EDITOR_ID + '/-/Custom_Max_Papers';
var ACTION_EDITORS_RECOMMENDATION_ID = ACTION_EDITOR_ID + '/-/Recommendation';
var ACTION_EDITORS_AVAILABILITY_ID = ACTION_EDITOR_ID + '/-/' + AVAILABILITY_NAME;
var REVIEWERS_REPORT_ID = REVIEWERS_ID + '/-/Reviewer_Report';

var REVIEWER_RATING_MAP = {
  "Exceeds expectations": 3,
  "Meets expectations": 2,
  "Falls below expectations": 1
}

var HEADER = {
  title: SHORT_PHRASE + ' Editors-in-Chief Console',
  instructions: ''
};
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
var RETRACTION_NAME = 'Retraction';
var RETRACTION_APPROVAL_NAME = 'Retraction_Approval';
var UNDER_REVIEW_STATUS = VENUE_ID + '/Under_Review';
var SUBMITTED_STATUS = VENUE_ID + '/Submitted';
var ASSIGNING_AE_STATUS = VENUE_ID + '/Assigning_AE';
var ASSIGNED_AE_STATUS = VENUE_ID + '/Assigned_AE';
var WITHDRAWN_STATUS = VENUE_ID + '/Withdrawn_Submission';
var RETRACTED_STATUS = VENUE_ID + '/Retracted_Acceptance';
var REJECTED_STATUS = VENUE_ID + '/Rejected';
var DESK_REJECTED_STATUS = VENUE_ID + '/Desk_Rejected'
var DECISION_PENDING_STATUS = VENUE_ID + '/Decision_Pending';

var referrerUrl = encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + ')');
var ae_url = '/edges/browse?traverse=' + ACTION_EDITORS_ASSIGNMENT_ID +
  '&edit=' + ACTION_EDITORS_ASSIGNMENT_ID + ';' + ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID + ',head:ignore' + ';' + ACTION_EDITORS_AVAILABILITY_ID + ',head:ignore' +
  '&browse=' + ACTION_EDITORS_ARCHIVED_ASSIGNMENT_ID + ';' + ACTION_EDITORS_AFFINITY_SCORE_ID +';' + ACTION_EDITORS_RECOMMENDATION_ID + ';' + ACTION_EDITORS_CONFLICT_ID + 
  '&version=2&referrer=' + referrerUrl;
var reviewers_url = '/edges/browse?traverse=' + REVIEWERS_ASSIGNMENT_ID +
  '&edit=' + REVIEWERS_ASSIGNMENT_ID + ';' + REVIEWERS_INVITE_ASSIGNMENT_ID + ';' + REVIEWERS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' + REVIEWERS_AVAILABILITY_ID + ',head:ignore' +
  '&browse=' + REVIEWERS_ARCHIVED_ASSIGNMENT_ID + ';' + REVIEWERS_AFFINITY_SCORE_ID+ ';' + REVIEWERS_CONFLICT_ID + ';' + REVIEWERS_PENDING_REVIEWS_ID + ',head:ignore;' + 
  '&version=2' +
  '&filter=' + REVIEWERS_PENDING_REVIEWS_ID + ' == 0 AND ' + REVIEWERS_AVAILABILITY_ID + ' == Available AND ' + REVIEWERS_CONFLICT_ID + ' == 0' +
  '&referrer=' + referrerUrl;  
HEADER.instructions = '<ul class="list-inline mb-0"><li><strong>Assignments Browser:</strong></li>' +
  '<li><a href="' + ae_url + '">Modify Action Editor Assignments</a></li>' +
  '<li><a href="' + reviewers_url + '">Modify Reviewer Assignments</a></li>' +
  '<li><a href="/assignments?group=' + ACTION_EDITOR_ID + '">Action Editor Proposed Assignments</a></li></ul>' +
  '<ul class="list-inline mb-0"><li><strong>Journal Request Forum:</strong></li>' +
  '<li><a href="/forum?id=' + JOURNAL_REQUEST_ID + '&referrer=' + referrerUrl + '">Recruit Reviewers/Action Editors</a></li></ul>' +
  '<ul class="list-inline mb-0"><li><strong>Reviewers Report:</strong></li>' +
  '<li><a href="/forum?id=' + REVIEWER_REPORT_ID + '&referrer=' + referrerUrl + '">Reviewers Report</a></li></ul>';

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
    if (invitationId.match(VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Reviewer_.*/-/Rating')) {
      invitations.push(invitationsById[invitationId]);
    }
  })
  return invitations;
}

var getRatingReplies = function(submission, ratingInvitations) {
  var ratingReplies = submission.details.replies.filter(function(reply) {
    return reply.invitations[0].includes('/-/Rating');
  });
  return ratingReplies;
}

// Main function is the entry point to the webfield code
var main = function() {
  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: [
      'Overview',
      'Submitted',
      'Under Review',
      'Under Discussion',
      'Under Decision',
      'Decision Pending',
      'Camera Ready',
      'All Submissions',
      'Action Editor Status',
      'Reviewer Status'
    ],
    referrer: args && args.referrer,
    fullWidth: true
  });
  
  if (!user || user.isGuest) {
    Webfield2.ui.errorMessage('You must be logged in to access this page.');
    return;
  }  

  loadData()
    .then(formatData)
    .then(renderData)
    .then(Webfield2.ui.done)
    .fail(Webfield2.ui.errorMessage);
};

var getGroupMembersCount = function(groupId) {
  if (!groupId) {
    return $.Deferred().resolve(0);
  }

  return Webfield.get('/groups', { id: groupId, limit: 1, select: 'members' }, { handleErrors: false })
    .then(function(result) {
      var members = _.get(result, 'groups[0].members', []);
      return members.length;
    }, function() {
      // Do not fail if group cannot be retreived
      return $.Deferred().resolve(0);
    });
};

var loadData = function() {
  return $.when(
    Webfield2.api.getGroupsByNumber(VENUE_ID, ACTION_EDITOR_NAME),
    Webfield2.api.getGroupsByNumber(VENUE_ID, REVIEWERS_NAME, { withProfiles: true}),
    Webfield2.api.getAllSubmissions(SUBMISSION_ID, { domain: VENUE_ID }),
    Webfield2.api.getAll('/notes', { forum: REVIEWER_ACKOWNLEDGEMENT_RESPONSIBILITY_ID, domain: VENUE_ID }),
    Webfield2.api.getAll('/notes', { forum: REVIEWER_REPORT_ID, domain: VENUE_ID })
    .then(function(notes) {
      return notes.reduce(function(content, currentValue) {
        var reviewer_id = currentValue.content.reviewer_id;
        if (reviewer_id) {
          if (!(reviewer_id.value in content)) {
            content[reviewer_id.value] = [];
          }
          content[reviewer_id.value].push(currentValue);
        }
        return content;
      }, {})
    }),
    Webfield2.api.getGroup(VENUE_ID + '/' + ACTION_EDITOR_NAME, { withProfiles: true}),
    Webfield2.api.getGroup(VENUE_ID + '/' + ACTION_EDITOR_NAME + '/Archived', { withProfiles: true}),
    Webfield2.api.getGroup(VENUE_ID + '/' + REVIEWERS_NAME, { withProfiles: true}),
    Webfield2.api.getGroup(VENUE_ID + '/' + REVIEWERS_NAME + '/Archived', { withProfiles: true}),
    Webfield2.api.getGroup(VENUE_ID + '/' + REVIEWERS_NAME + '/Volunteers', { withProfiles: true}),
    Webfield2.api.getAll('/invitations', {
      prefix: VENUE_ID + '/' + SUBMISSION_GROUP_NAME,
      type: 'all',
      select: 'id,cdate,duedate,expdate',
      sort: 'cdate:asc',
      domain: VENUE_ID
    }).then(function(invitations) {
      return _.keyBy(invitations, 'id');
    }),
    Webfield2.api.getAll('/invitations', { prefix: VENUE_ID + '/-/.*', select: 'id', expired: true, sort: 'cdate:asc', domain: VENUE_ID }),
    Webfield2.api.getAll('/invitations', { prefix: REVIEWERS_ID + '/-/.*', select: 'id', expired: true, sort: 'cdate:asc', domain: VENUE_ID }),
    Webfield2.api.getAll('/invitations', { prefix: ACTION_EDITOR_ID + '/-/.*', select: 'id', expired: true, sort: 'cdate:asc', domain: VENUE_ID }),
    Webfield2.api.get('/edges', { invitation: ACTION_EDITORS_RECOMMENDATION_ID, groupBy: 'head', select: 'count', domain: VENUE_ID})
    .then(function(response) {
      var groupedEdges = response.groupedEdges;
      var recommendationCount = {};
      groupedEdges.forEach(function(group){
        recommendationCount[group.id.head] = group.count;
      })
      return recommendationCount;
    })
  );
};

var updateEarlyLateTaskDuedate = function(earlylateTaskDueDate, task) {
  if ((earlylateTaskDueDate == 0 || earlylateTaskDueDate > task.duedate) && !task.complete) {
    earlylateTaskDueDate = task.duedate;
  }
  return earlylateTaskDueDate;
}

var formatData = function(
  aeByNumber,
  reviewersByNumber,
  submissions,
  responsibilityNotes,
  reviewerReportByReviewerId,
  actionEditors,
  archivedActionEditors,
  reviewers,
  archivedReviewers,
  volunteerReviewers,
  invitationsById,
  superInvitationIds,
  reviewerInvitationIds,
  aeInvitationIds,
  aeRecommendations
) {
  var referrerUrl = encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + '#paper-status)');

  var reviewerStatusById = {};
  var getReviewerStatus = function(reviewer, index, isOfficial, isArchived, isVolunteer) {
    var responsibility = responsibilityNotes.find(function(reply) {
      return reply.invitations[0] === REVIEWERS_ID + '/-/' + reviewer.id + '/' + RESPONSIBILITY_ACK_NAME;
    });
    var reviewerReports = reviewerReportByReviewerId[reviewer.id] || [];

    return {
      index: { number: index + 1 },
      summary: {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
        status: {
          Profile: reviewer.id.startsWith('~') ? 'Yes' : 'No',
          Publications: '-',
          'Responsibility Acknowledgement': responsibility ? 'Yes' : 'No',
          'Reviewer Report': reviewerReports.length,
          Official: isOfficial ? 'Yes' : 'No',
          Archived: isArchived ? 'Yes' : 'No',
          Volunteer: isVolunteer ? 'Yes' : 'No'
        }
      },
      reviewerProgressData: {
        numCompletedReviews: 0,
        numPapers: 0,
        papers: [],
        referrer: referrerUrl
      },
      ratingData: {
        ratings:[],
        ratingsMap: Object.keys(REVIEWER_RATING_MAP).reduce((o, key) => Object.assign(o, {[key]: 0}), {}),
        averageRating: 0
      },
      reviewerStatusData: {
        numCompletedReviews: 0,
        numPapers: 0,
        papers: [],
        referrer: referrerUrl
      },
      note: {id: reviewer.id}
    };
  }
  var officialReviewerIds = new Set();
  var archivedReviewerIds = new Set();
  reviewers.members.forEach(function(reviewer, index) {
    reviewerStatusById[reviewer.id] = getReviewerStatus(reviewer, index, true, false, false);
    officialReviewerIds.add(reviewer.id);
  });

  (archivedReviewers?.members || []).forEach(function(reviewer, index) {
    reviewerStatusById[reviewer.id] = getReviewerStatus(reviewer, index, false, true, false);
    archivedReviewerIds.add(reviewer.id);
  });

  (volunteerReviewers?.members || []).forEach(function(reviewer, index) {
    reviewerStatusById[reviewer.id] = getReviewerStatus(reviewer, index, officialReviewerIds.has(reviewer.id), archivedReviewerIds.has(reviewer.id), true);
  });  

  var actionEditorStatusById = {};
  actionEditors.members.forEach(function(actionEditor, index) {
    actionEditorStatusById[actionEditor.id] = {
      index: { number: index + 1 },
      summary: {
        id: actionEditor.id,
        name: actionEditor.name,
        email: actionEditor.email,
        status: {
          Profile: actionEditor.id.startsWith('~') ? 'Yes' : 'No',
          Publications: '-'
        }
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

  archivedActionEditors.members.forEach(function(actionEditor, index) {
    actionEditorStatusById[actionEditor.id] = {
      index: { number: index + 1 },
      summary: {
        id: actionEditor.id,
        name: actionEditor.name,
        email: actionEditor.email,
        status: {
          Profile: actionEditor.id.startsWith('~') ? 'Yes' : 'No',
          Publications: '-',
          Archived: 'Yes'
        }
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

  var paperStatusRows = [];
  var authorSubmissionsCount = {};
  var incompleteEicTasks = [];
  var overdueTasks = [];
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
    var paperActionEditors = aeByNumber[number] || [];
    var actionEditor = { id: 'No Action Editor' };
    if (paperActionEditors.length && actionEditorStatusById[paperActionEditors[0].id]) {
      actionEditor = actionEditorStatusById[paperActionEditors[0].id].summary;
    }

    // Track number of submissions per author
    if (
      formattedSubmission.content.venueid === UNDER_REVIEW_STATUS &&
      formattedSubmission.content.authorids &&
      formattedSubmission.content.authorids.length
    ) {
      formattedSubmission.content.authorids.forEach(function(profileId) {
        authorSubmissionsCount[profileId] = authorSubmissionsCount[profileId] || 0;
        authorSubmissionsCount[profileId] += 1;
      });
    }

    // Build array of tasks
    var tasks = [];
    // AE Recommendation by Authors
    var aeRecommendationInvitation = invitationsById[getInvitationId(number, RECOMMENDATION_NAME, ACTION_EDITOR_NAME)];
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
    var cameraReadyTask = null;
    var cameraReadyVerificationTask = null;
    // Retraction by Authors
    var retractionInvitation = invitationsById[getInvitationId(number, RETRACTION_NAME)];
    var retractionNotes = getReplies(submission, RETRACTION_NAME);
    // Retraction Approval by EIC
    var retractionApprovalInvitation = invitationsById[getInvitationId(number, RETRACTION_APPROVAL_NAME)];
    var retractionApprovalNotes = getReplies(submission, RETRACTION_APPROVAL_NAME);

    var earlylateTaskDueDate = 0;

    if (aeRecommendationInvitation) {
      var recommendationCount = aeRecommendations[submission.id] || 0;
      var task = {
        id: aeRecommendationInvitation.id,
        cdate: aeRecommendationInvitation.cdate,
        duedate: aeRecommendationInvitation.duedate,
        complete: recommendationCount >= NUMBER_OF_REVIEWERS,
        replies: Array(recommendationCount).fill(1)
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);
    }

    if (reviewApprovalInvitation) {
      var task = {
        id: reviewApprovalInvitation.id,
        cdate: reviewApprovalInvitation.cdate,
        duedate: reviewApprovalInvitation.duedate,
        complete: reviewApprovalNotes.length > 0,
        replies: reviewApprovalNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);
    }

    if (deskRejectionApprovalInvitation) {
      var task = {
        id: deskRejectionApprovalInvitation.id,
        cdate: deskRejectionApprovalInvitation.cdate,
        duedate: deskRejectionApprovalInvitation.duedate,
        complete: deskRejectionApprovalNotes.length > 0,
        replies: deskRejectionApprovalNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);
      if (!task.complete) {
        incompleteEicTasks.push([
          {
            id: formattedSubmission.id,
            title: formattedSubmission.content.title || formattedSubmission.number
          },
          task
        ]);
      }      
    }

    if (reviewerAssignmentInvitation) {
      var reviewers = reviewersByNumber[number] || [];
      var task = {
        id: reviewerAssignmentInvitation.id,
        cdate: reviewerAssignmentInvitation.cdate,
        duedate: reviewerAssignmentInvitation.duedate,
        complete: reviewers.length >= NUMBER_OF_REVIEWERS,
        replies: reviewers
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);     
    }

    if (reviewInvitation) {
      var task = {
        id: reviewInvitation.id,
        cdate: reviewInvitation.cdate,
        duedate: reviewInvitation.duedate,
        complete: reviewNotes.length >= NUMBER_OF_REVIEWERS,
        replies: reviewNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);         
    }

    if (officialRecommendationInvitation) {
      var task = {
        id: officialRecommendationInvitation.id,
        cdate: officialRecommendationInvitation.cdate,
        duedate: officialRecommendationInvitation.duedate,
        complete: officialRecommendationNotes.length >= NUMBER_OF_REVIEWERS,
        replies: officialRecommendationNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);       
    }

    if (reviewerRatingInvitations.length) {
      var task = {
        id: getInvitationId(number, 'Reviewer_Rating'),
        cdate: reviewerRatingInvitations[0].cdate,
        duedate: reviewerRatingInvitations[0].duedate,
        complete: reviewerRatingReplies.length == reviewNotes.length,
        replies: reviewerRatingReplies
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);      
    }

    if (decisionInvitation) {
      var task = {
        id: decisionInvitation.id,
        cdate: decisionInvitation.cdate,
        duedate: decisionInvitation.duedate,
        complete: decisionNotes.length > 0,
        replies: decisionNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);      
    }

    if (decisionApprovalInvitation) {
      var task = {
        id: decisionApprovalInvitation.id,
        cdate: decisionApprovalInvitation.cdate,
        duedate: decisionApprovalInvitation.duedate,
        complete: decisionApprovalNotes.length > 0,
        replies: decisionApprovalNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);      
      if (!task.complete) {
        incompleteEicTasks.push([
          {
            id: formattedSubmission.id,
            title: formattedSubmission.content.title || formattedSubmission.number
          },
          task
        ]);
      }
    }

    if (cameraReadyRevisionInvitation) {
      var complete = submission.invitations.includes(cameraReadyRevisionInvitation.id);
      cameraReadyTask = {
        id: cameraReadyRevisionInvitation.id,
        cdate: cameraReadyRevisionInvitation.cdate,
        duedate: cameraReadyRevisionInvitation.duedate,
        complete: complete,
        replies: complete ? [1] : []
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, cameraReadyTask);
      tasks.push(cameraReadyTask);      
    }

    if (cameraReadyVerificationInvitation) {
      cameraReadyVerificationTask = {
        id: cameraReadyVerificationInvitation.id,
        cdate: cameraReadyVerificationInvitation.cdate,
        duedate: cameraReadyVerificationInvitation.duedate,
        complete: cameraReadyVerificationNotes.length > 0,
        replies: cameraReadyVerificationNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, cameraReadyVerificationTask);
      tasks.push(cameraReadyVerificationTask);      
    }

    if (retractionApprovalInvitation) {
      var task = {
        id: retractionApprovalInvitation.id,
        cdate: retractionApprovalInvitation.cdate,
        duedate: retractionApprovalInvitation.duedate,
        complete: retractionApprovalNotes.length > 0,
        replies: retractionApprovalNotes
      };
      earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
      tasks.push(task);      
      if (!task.complete) {
        incompleteEicTasks.push([
          {
            id: formattedSubmission.id,
            title: formattedSubmission.content.title || formattedSubmission.number
          },
          task
        ]);
      }
    }    

    var reviews = reviewNotes;
    var recommendations = officialRecommendationNotes;
    var recommendationByReviewer = {};
    recommendations.forEach(function(recommendation) {
      recommendationByReviewer[recommendation.signatures[0]] = recommendation;
    });
    var decisions = decisionNotes;
    var paperReviewers = reviewersByNumber[number] || [];
    var paperReviewerStatus = {};
    var completedReviews = reviews.length && (reviews.length == paperReviewers.length);

    paperReviewers.forEach(function(reviewer) {
      var completedReview = reviews.find(function(review) { return review.signatures[0].endsWith('/Reviewer_' + reviewer.anonId); });
      var assignmentAcknowledgement = getReplies(submission, reviewer.id + '/' + ASSIGNMENT_ACKNOWLEDGEMENT_NAME, REVIEWERS_NAME);
      var reviewerRecommendation = null;
      var status = {};
      var reviewerStatus = reviewerStatusById[reviewer.id];
      var links = {
        'Report': '/forum?id=' + REVIEWER_REPORT_ID + '&noteId=' + REVIEWER_REPORT_ID + '&invitationId=' + REVIEWERS_REPORT_ID + '&edit.note.content.reviewer_id=' + reviewer.id + '&referrer=' + referrerUrl,
      }      

      if (assignmentAcknowledgement && assignmentAcknowledgement.length) {
        status.Acknowledged = 'Yes';
      }

      if (completedReview) {
        reviewerRecommendation = recommendationByReviewer[completedReview.signatures[0]];
        if (reviewerRecommendation) {
          status.Recommendation = reviewerRecommendation.content.decision_recommendation?.value || 'Yes';
          status.Certifications = reviewerRecommendation.content.certification_recommendations ? reviewerRecommendation.content.certification_recommendations.value.join(', ') : '';
        }
        var reviewerRating = reviewerRatingReplies.find(function (p) {
          return p.replyto === completedReview.id;
        });
        if(reviewerRating){
          status.Rating = reviewerRating.content.rating.value;
          if(reviewerStatus){
            var rating = reviewerRating.content.rating.value;
            var ratingValue = REVIEWER_RATING_MAP[rating];
            reviewerStatus.ratingData.ratings.push(rating);
            reviewerStatus.ratingData.ratingsMap[rating] += 1;
            var count = reviewerStatus.ratingData.ratings.length;
            if (count > 1) {
              reviewerStatus.ratingData.averageRating = ((reviewerStatus.ratingData.averageRating * (count - 1) + ratingValue) / count);
            } else {
              reviewerStatus.ratingData.averageRating = ratingValue;
            }
          }
        }
      }
      paperReviewerStatus[reviewer.anonId] = {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
        completedReview: completedReview && true,
        completedRecommendation: reviewerRecommendation && true,
        hasRecommendationStarted: officialRecommendationInvitation && officialRecommendationInvitation.cdate < Date.now(),
        forum: submission.id,
        note: completedReview && completedReview.id,
        status: status,
        links: links,
        forumUrl: 'https://openreview.net/forum?' + $.param({
          id: submission.id,
          noteId: submission.id,
          invitationId: getInvitationId(submission.number, REVIEW_NAME)
        }),
        anonymousGroupId: reviewer.anonymousGroupId
      }

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
    });

    paperActionEditors.forEach(function(actionEditor) {
      var completedDecision = decisions.find(function(decision) { return decision.signatures[0].startsWith(VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Action_Editor'); });
      var actionEditorStatus = actionEditorStatusById[actionEditor.id];
      if (actionEditorStatus) {
        actionEditorStatus.reviewProgressData.numPapers += 1;
        actionEditorStatus.decisionProgressData.numPapers += 1;
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
    });

    var metaReview = null;
    var decision = decisions.length > 0 ? decisions[0] : null;
    if (decision) {
      metaReview = {
        id: decision.id,
        forum: submission.id,
        content: {
          recommendation: decision.content.recommendation.value,
          certification: (decision.content.certifications && decision.content.certifications.value) || []
        }
      };
    }

    overdueTasks.concat(tasks.filter(function(inv) { return !inv.complete; }));

    var aeActions = [UNDER_REVIEW_STATUS, SUBMITTED_STATUS, ASSIGNED_AE_STATUS, ASSIGNING_AE_STATUS].includes(submission.content.venueid.value) ? [
      {
        name: 'Edit Assignments',
        url: '/edges/browse?start=staticList,type:head,ids:' + submission.id +
        '&traverse=' + ACTION_EDITORS_ASSIGNMENT_ID +
        '&edit=' + ACTION_EDITORS_ASSIGNMENT_ID + ';' + ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' + ACTION_EDITORS_AVAILABILITY_ID + ',head:ignore' +
        '&browse=' + ACTION_EDITORS_ARCHIVED_ASSIGNMENT_ID + ';' + ACTION_EDITORS_AFFINITY_SCORE_ID + ';' + ACTION_EDITORS_RECOMMENDATION_ID + ';' + ACTION_EDITORS_CONFLICT_ID + ';' + 
        '&version=2'
      }
    ] : [];
    if (submission.content['previous_' + VENUE_ID + '_submission_url']) {
      aeActions.push({
        name: 'TMLR Resubmission',
        url: submission.content['previous_' + VENUE_ID + '_submission_url']['value']
      })
    }

    paperStatusRows.push({
      checked: { noteId: submission.id, checked: false },
      submissionNumber: { number: parseInt(number, 10) },
      submission: formattedSubmission,
      reviewProgressData: {
        noteId: submission.id,
        paperNumber: number,
        numSubmittedReviews: reviews.length,
        numSubmittedRecommendations: recommendations.length,
        numReviewers: paperReviewers.length,
        reviewers: paperReviewerStatus,
        expandReviewerList: true,
        sendReminder: true,
        showPreferredEmail: PREFERRED_EMAILS_ID,
        referrer: referrerUrl,
        actions: ([UNDER_REVIEW_STATUS].includes(submission.content.venueid.value) && reviewerAssignmentInvitation) ? [
          {
            name: 'Edit Assignments',
            url: '/edges/browse?start=staticList,type:head,ids:' + submission.id +
            '&traverse='+ REVIEWERS_ASSIGNMENT_ID +
            '&edit='+ REVIEWERS_ASSIGNMENT_ID + ';' + REVIEWERS_INVITE_ASSIGNMENT_ID + ';' + REVIEWERS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' + REVIEWERS_AVAILABILITY_ID + ',head:ignore' +
            '&browse=' + REVIEWERS_ARCHIVED_ASSIGNMENT_ID + ';' + REVIEWERS_AFFINITY_SCORE_ID + ';' + REVIEWERS_CONFLICT_ID + ';' + REVIEWERS_PENDING_REVIEWS_ID + ',head:ignore;' + 
            '&version=2' +
            '&filter=' + REVIEWERS_PENDING_REVIEWS_ID + ' == 0 AND ' + REVIEWERS_AVAILABILITY_ID + ' == Available AND ' + REVIEWERS_CONFLICT_ID + ' == 0'
          }
        ] : [],
        duedate: reviewInvitation && reviewInvitation.duedate || 0
      },
      actionEditorProgressData: {
        recommendation: metaReview && metaReview.content.recommendation,
        status: {
          Certification: metaReview ? metaReview.content.certification.join(', ') : ''
        },
        numMetaReview: metaReview ? 'One' : 'No',
        areachair: !actionEditor.name ? { name: 'No Action Editor' } : { id: actionEditor.id, name: actionEditor.name },
        actionEditor: actionEditor,
        metaReview: metaReview,
        referrer: referrerUrl,
        reviewPending: reviewInvitation && reviewNotes.length < NUMBER_OF_REVIEWERS,
        recommendationPending: officialRecommendationInvitation && officialRecommendationNotes.length < NUMBER_OF_REVIEWERS && decisionNotes.length == 0,
        ratingPending: reviewerRatingInvitations.length && reviewerRatingReplies.length < reviewNotes.length,
        decisionPending: decisionInvitation && decisionNotes.length == 0,
        decisionApprovalPending: metaReview && decisionApprovalNotes.length == 0,
        cameraReadyPending: (cameraReadyTask && !cameraReadyTask.complete) || (cameraReadyVerificationTask && !cameraReadyVerificationTask.complete),
        earlylateTaskDueDate: earlylateTaskDueDate,
        metaReviewName: 'Decision',
        committeeName: 'Action Editor',
        actions: aeActions,
        tableWidth: '100%',
        showPreferredEmail: PREFERRED_EMAILS_ID,
      },
      tasks: { invitations: tasks, forumId: submission.id },
      eicComments: {
        comments: submission.details.replies.filter(function(r) {
          return r.readers.length == 1 && r.readers[0] == EDITORS_IN_CHIEF_ID;
        }).sort(function(a, b) {
          return a.tcdate - b.tcdate;
        })
      },
      status: submission.content.venue?.value
    });
  });

  var submittedStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === SUBMITTED_STATUS
    || row.submission.content.venueid === ASSIGNING_AE_STATUS
    || row.submission.content.venueid === ASSIGNED_AE_STATUS;
  });
  var underReviewStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === UNDER_REVIEW_STATUS
      && row.actionEditorProgressData.reviewPending;
  });
  var underDiscussionStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === UNDER_REVIEW_STATUS
      && row.actionEditorProgressData.recommendationPending;
  });
  var underDecisionStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === UNDER_REVIEW_STATUS
      && (row.actionEditorProgressData.ratingPending || row.actionEditorProgressData.decisionPending || row.actionEditorProgressData.decisionApprovalPending);
  });
  var decisionPendingStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === DECISION_PENDING_STATUS
      && row.actionEditorProgressData.decisionApprovalPending;
  });
  var cameraReadyStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === DECISION_PENDING_STATUS
      && row.actionEditorProgressData.cameraReadyPending;
  });
  var submissionStatusRows = paperStatusRows;
  var acceptedStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === VENUE_ID;
  });  

  var withdrawnStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === WITHDRAWN_STATUS;
  });
  var retractedStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === RETRACTED_STATUS;
  });
  var rejectedStatusRows = paperStatusRows.filter(function(row) {
    return row.submission.content.venueid === REJECTED_STATUS
      || row.submission.content.venueid === DESK_REJECTED_STATUS;
  });

  // Generate journal stats for overview tab
  var journalStats = {
    numReviewers: reviewers.members.length,
    numActionEditors: actionEditors.members.length,
    numSubmitted: submittedStatusRows.length,
    numUnderReview: underReviewStatusRows.length,
    numUnderDiscussion: underDiscussionStatusRows.length,
    numUnderDecision: underDecisionStatusRows.length,
    numAccepted: acceptedStatusRows.length,
    numWithdrawn: withdrawnStatusRows.length,
    numRetracted: retractedStatusRows.length,
    numRejected: rejectedStatusRows.length,
    superInvitationIds: superInvitationIds,
    reviewerInvitationIds: reviewerInvitationIds.filter(function(inv) {
      return !inv.id.endsWith('/' + RESPONSIBILITY_ACK_NAME);
    }),
    aeInvitationIds: aeInvitationIds,
    activeAuthors: _.sortBy(
      _.toPairs(authorSubmissionsCount),
      function(pair) { return pair[1]; }
    ).reverse().slice(0, 20),
    incompleteEicTasks: incompleteEicTasks.sort(
      function(a, b) { return a[1].duedate - b[1].duedate; }
    ),
    overdueTasks: overdueTasks.sort(
      function(a, b) { return a[1].duedate - b[1].duedate; }
    ).slice(0, 20),
  };

  return {
    submittedStatusRows: submittedStatusRows,
    submissionStatusRows: submissionStatusRows,
    underReviewStatusRows: underReviewStatusRows,
    underDiscussionStatusRows: underDiscussionStatusRows,
    underDecisionStatusRows: underDecisionStatusRows,
    decisionPendingStatusRows: decisionPendingStatusRows,
    cameraReadyStatusRows: cameraReadyStatusRows,
    reviewerStatusRows: Object.values(reviewerStatusById),
    actionEditorStatusRows: Object.values(actionEditorStatusById),
    journalStats: journalStats,
  };
};

// Render functions
var renderTable = function(container, rows) {
  Webfield2.ui.renderTable('#' + container, rows, {
    headings: [
      '<input type="checkbox" class="select-all-papers">',
      '#',
      'Paper Summary',
      'Review Progress',
      'Action Editor Decision',
      'Tasks',
      'EIC Comments',
      'Status'
    ],
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
      Handlebars.templates.noteAreaChairs,
      function(data) {
        return Webfield2.ui.eicTaskList(data.invitations, data.forumId, {
          referrer: encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + ')'),
          showEditLink: true
        });
      },
      function(data) {
        var html = data.comments.map(function(c) {
          return (
            '<li class="mb-3">' +
              '<p class="text-muted mb-1">' + view.forumDate(c.tcdate) + ': </p>' +
              '<p class="mb-1" style="white-space: nowrap; text-overflow: ellipsis; overflow: hidden;"><strong><a href="https://openreview.net/forum?id=' + c.forum + '&noteId=' + c.id + '" target="_blank" rel="nofollow">' + c.content.title.value + '</a></strong></p>' +
              '<p style="word-break: break-word;">' + c.content.comment.value + '</p>' +
            '</li>'
          );
        });
        return  '<ul class="list-unstyled">' + html.join('\n') + '</ul>';
      },
      function(data) {
        return '<h4>' + data + '</h4>';
      }
    ],
    sortOptions: {
      Paper_Number: function(row) { return row.submissionNumber.number; },
      Paper_Title: function(row) { return _.toLower(_.trim(row.submission.content.title)); },
      Paper_Submission_Date: function(row) { return row.submission.cdate; },
      Number_of_Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
      Number_of_Reviews_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedReviews; },
      Number_of_Recommendations_Submitted: function(row) { return row.reviewProgressData.numSubmittedRecommendations; },
      Number_of_Recommendations_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedRecommendations; },
      Decision: function(row) { return row.actionEditorProgressData.recommendation; },
      Status: function(row) { return row.status; },
      Review_Due_Date: function(row) { return row.reviewProgressData.duedate; },
      Earliest_Late_Due_Date: function(row) { return row.actionEditorProgressData.earlylateTaskDueDate; }
    },
    searchProperties: {
      number: ['submissionNumber.number'],
      id: ['submission.id'],
      title: ['submission.content.title'],
      submissionDate: ['submission.cdate'],
      author: ['submission.content.authors', 'note.content.authorids'], // multi props
      keywords: ['submission.content.keywords'],
      reviewer: ['reviewProgressData.reviewers'],
      numReviewersAssigned: ['reviewProgressData.numReviewers'],
      numReviewsDone: ['reviewProgressData.numSubmittedReviews'],
      numRecommendationsDone: ['reviewProgressData.numSubmittedRecommendations'],
      decision: ['actionEditorProgressData.recommendation'],
      status: ['status'],
      default: ['submissionNumber.number', 'submission.content.title'],
      certifications: ['submission.content.certifications'],
    },
    reminderOptions: {
      container: 'a.send-reminder-link',
      defaultSubject: SHORT_PHRASE + ' Reminder',
      defaultBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the submission page:\n\n{{forumUrl}}\n\n' +
        'Thank you,\n' + SHORT_PHRASE + ' Editor-in-Chief',
      replyTo: EDITORS_IN_CHIEF_EMAIL,
      messageInvitationId: VENUE_ID + '/-/Edit',
      messageSignature: VENUE_ID,
      menu: [{
        id: 'all-reviewers',
        name: 'All reviewers of selected papers',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return rows.map(function(row) {
            return {
              groups: selectedIds.includes(row.submission.id)
                ? Object.values(row.reviewProgressData.reviewers)
                : [],
              forumUrl: 'https://openreview.net/forum?' + $.param({
                id: row.submission.forum
              })
            }
          });
        },
        messageBody: 'This is the message body'
      },
      {
        id: 'all-action-editors',
        name: 'All action editors of selected papers',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return rows.map(function(row) {
            return {
              groups: selectedIds.includes(row.submission.id)
                ? [row.actionEditorProgressData.actionEditor]
                : [],
              forumUrl: 'https://openreview.net/forum?' + $.param({
                id: row.submission.forum
              })
            }
          });
        },
        messageBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your decision for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the submission page:\n\n{{forumUrl}}\n\n' +
        'Thank you,\n' + SHORT_PHRASE + ' Editor-in-Chief'
      },
      {
        id: 'all-authors',
        name: 'All authors of selected papers',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return rows.map(function(row) {
            return {
              groups: selectedIds.includes(row.submission.id)
                ? row.submission.content.authorids.map(function(authorId) { return { id: authorId, name: view.prettyId(authorId), email: authorId };})
                : [],
              forumUrl: 'https://openreview.net/forum?' + $.param({
                id: row.submission.forum
              })
            }
          });
        },
        messageBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your camera ready revision for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the submission page:\n\n{{forumUrl}}\n\n' +
        'Thank you,\n' + SHORT_PHRASE + ' Editor-in-Chief',
      },
      {
        id: 'unsubmitted-reviews',
        name: 'Reviewers with missing reviews',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return rows.map(function(row) {
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
              })
            }
          });
        }
      }, {
        id: 'unsubmitted-recommendations',
        name: 'Reviewers with missing official recommendations',
        getUsers: function(selectedIds) {
          selectedIds = selectedIds || [];
          return rows.map(function(row) {
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
              })
            }
          });
        }
      }]
    },
    extraClasses: 'console-table paper-table',
    pageSize: 10,
    postRenderTable: function() {
      $('#' + container + ' .console-table th').eq(0).css('width', '2%');  // [ ]
      $('#' + container + ' .console-table th').eq(1).css('width', '3%');  // #
      $('#' + container + ' .console-table th').eq(2).css('width', '20%'); // Paper Summary
      $('#' + container + ' .console-table th').eq(3).css('width', '20%'); // Review Progress
      $('#' + container + ' .console-table th').eq(4).css('width', '20%'); // Action Editor Decision
      $('#' + container + ' .console-table th').eq(5).css('width', '20%'); // Tasks
      $('#' + container + ' .console-table th').eq(6).css('width', '15%'); // EIC comments
      $('#' + container + ' .console-table th').eq(7).css('width', '11%'); // Status
    },
    preferredEmailsInvitationId: PREFERRED_EMAILS_ID
  });
};

var renderOverviewTab = function(conferenceStats) {
  var referrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + EDITORS_IN_CHIEF_ID + '#paper-status)');

  var renderStatContainer = function(title, stat, hint, extraClasses) {
    return '<div class="col-md-4 col-xs-6 mb-3 ' + (extraClasses || '') + '">' +
      '<h4>' + title + '</h4>' +
      stat +
      (hint ? '<p class="hint">' + hint + '</p>' : '') +
      '</div>';
  };

  var getDueDateStatus = function(date) {
    var day = 24 * 60 * 60 * 1000;
    var diff = Date.now() - date.getTime();

    if (diff > 0) {
      return 'expired';
    }
    if (diff > -3 * day) {
      return 'warning';
    }
    return '';
  };

  var renderCombinedTasksList = function(invPairs) {
    var resultHtml = '';
    if (invPairs.length > 0) {
      resultHtml += '<ul class="list-unstyled submissions-list task-list eic-task-list mt-0 mb-0">'
      invPairs.forEach(function(forumInv) {
        var dateFormatOptions = {
          hour: 'numeric', minute: 'numeric', day: '2-digit', month: 'short', year: 'numeric', timeZoneName: 'long'
        };
        var inv = forumInv[1]

        if (inv.cdate > Date.now()) {
          var startDate = new Date(inv.cdate);
          inv.startDateStr = startDate.toLocaleDateString('en-GB', dateFormatOptions);
        }
        var duedate = new Date(inv.duedate);
        inv.dueDateStr = duedate.toLocaleDateString('en-GB', dateFormatOptions);
        inv.dueDateStatus = getDueDateStatus(duedate);
        resultHtml += (
          '<li class="note">' +
            '<p class="mb-1"><strong><a href="/forum?id=' + forumInv[0].id + '&invitationId=' + inv.id + '&referrer=' + referrerUrl + '" target="_blank">' +
            forumInv[0].title + ': ' + view.prettyInvitationId(inv.id) +
            '</a></strong></p>' +
            (inv.startDateStr ? '<p class="mb-1"><span class="duedate" style="margin-left: 0;">Start: ' + inv.startDateStr + '</span></p>' : '') +
            '<p class="mb-1"><span class="duedate ' + inv.dueDateStatus +'" style="margin-left: 0;">Due: ' + inv.dueDateStr + '</span></p>' +
          '</li>'
        );
      });
      resultHtml += '</ul>';
    } else {
      resultHtml += '<p class="empty-message mb-3">No tasks to complete.</p>';
    }
    return resultHtml;
  }

  // Conference statistics
  var html = '<div class="container"><div class="row text-center" style="margin-top: .5rem;">';
  html += renderStatContainer(
    'Reviewers:',
    '<h3>' + conferenceStats.numReviewers + '</h3>',
    '<a href="/group/edit?id=' + REVIEWERS_ID + '">Reviewers Group</a> (<a href="/group/edit?id=' + REVIEWERS_ID + '/Invited">Invited</a>, <a href="/group/edit?id=' + REVIEWERS_ID + '/Declined">Declined</a>)',
    'col-md-offset-2'
  );
  html += renderStatContainer(
    'Action Editors:',
    '<h3>' + conferenceStats.numActionEditors + '</h3>',
    '<a href="/group/edit?id=' + ACTION_EDITOR_ID + '">Action Editors Group</a> (<a href="/group/edit?id=' + ACTION_EDITOR_ID + '/Invited">Invited</a>, <a href="/group/edit?id=' + ACTION_EDITOR_ID + '/Declined">Declined</a>)'
  );
  html += '</div>';
  html += '<hr class="spacer" style="margin-bottom: 1rem; margin-top: .5rem;">';

  html += '<div class="row text-center" style="margin-top: .5rem;">';
  html += renderStatContainer(
    'Submitted Papers:',
    '<h3>' + conferenceStats.numSubmitted + '</h3>'
  );
  html += renderStatContainer(
    'Papers Under Review:',
    '<h3>' + conferenceStats.numUnderReview + '</h3>'
  );
  html += renderStatContainer(
    'Papers Under Discussion:',
    '<h3>' + conferenceStats.numUnderDiscussion + '</h3>'
  );
  html += renderStatContainer(
    'Papers Under Decision:',
    '<h3>' + conferenceStats.numUnderDecision + '</h3>'
  );
  html += renderStatContainer(
    'Accepted Papers:',
    '<h3>' + conferenceStats.numAccepted + '</h3>'
  );
  html += renderStatContainer(
    'Withdrawn Papers:',
    '<h3>' + conferenceStats.numWithdrawn + '</h3>'
  );
  html += renderStatContainer(
    'Rejected Papers:',
    '<h3>' + conferenceStats.numRejected + '</h3>'
  );
  html += renderStatContainer(
    'Retracted Papers:',
    '<h3>' + conferenceStats.numRetracted + '</h3>'
  );
  html += '</div>';
  html += '<hr class="spacer" style="margin-bottom: 1rem; margin-top: 0;">';

  html += '<div class="row" style="margin-top: .5rem;">';
  html += '<div class="col-md-4 col-xs-6">';
  html += '<h4>Important Invitations:</h4>';
  html += '<p class="mb-1"><strong>Venue:</strong></p>';
  html += '<ul style="padding-left: 15px">';
  html += conferenceStats.superInvitationIds.map(function(inv) {
    return '<li><a href="/invitation/edit?id=' + inv.id + '">' + view.prettyInvitationId(inv.id) + '</a></li>';
  }).join('\n');
  html += '</ul>';
  html += '<p class="mb-1"><strong>Reviewers:</strong></p>';
  html += '<ul style="padding-left: 15px">';
  html += conferenceStats.reviewerInvitationIds.map(function(inv) {
    return '<li><a href="/invitation/edit?id=' + inv.id + '">' + view.prettyInvitationId(inv.id) + '</a></li>';
  }).join('\n');
  html += '</ul>';
  html += '<p class="mb-1"><strong>Action Editors:</strong></p>';
  html += '<ul style="padding-left: 15px">';
  html += conferenceStats.aeInvitationIds.map(function(inv) {
    return '<li><a href="/invitation/edit?id=' + inv.id + '">' + view.prettyInvitationId(inv.id) + '</a></li>';
  }).join('\n');
  html += '</ul>';
  html += '</div>';

  html += '<div class="col-md-4 col-xs-6">';
  html += '<h4>Authors with Most Submissions:</h4>';
  html += '<table class="table table-condensed table-minimal">';
  html += '<thead><tr>' +
    '<th style="width: 35px;height: 20px;padding: 0;border: 0;">#</th>' +
    '<th style="height: 20px;padding: 0;border: 0;">Author</th>' +
    '<th style="width: 120px;height: 20px;padding: 0;border: 0;">All Submissions</th>' +
    '</tr></thead>';
  html += '<tbody>';
  html += conferenceStats.activeAuthors.map(function(entry) {
    return '<tr>' +
      '<td style="padding-left: 0;font-size: .875rem;">' + entry[1] + '</td>' +
      '<td style="padding-left: 0;font-size: .875rem;"><a href="/profile?id=' + entry[0] + '">' + view.prettyId(entry[0]) + '</a></td>' +
      '<td style="padding-left: 0;font-size: .875rem;"><a href="/search?term=' + entry[0] + '&group=' + VENUE_ID + '&content=all&source=forum">view &raquo;</a></td>' +
      '</tr>';
  }).join('\n');
  html += '</tbody>';
  html += '</table>';
  html += '</div>';

  html += '<div class="col-md-4 col-xs-6">';
  html += '<h4>Pending Editors-in-Chief Tasks:</h4>';
  html += renderCombinedTasksList(conferenceStats.incompleteEicTasks);

  html += '<h4>Overdue Tasks:</h4>';
  html += renderCombinedTasksList(conferenceStats.overdueTasks);
  html += '</div>';

  html += '</div></div>';

  $('#overview').html(html);
};

var renderData = function(venueStatusData) {
  renderOverviewTab(venueStatusData.journalStats);

  renderTable('submitted', venueStatusData.submittedStatusRows);
  renderTable('under-review', venueStatusData.underReviewStatusRows);
  renderTable('under-discussion', venueStatusData.underDiscussionStatusRows);
  renderTable('under-decision', venueStatusData.underDecisionStatusRows);
  renderTable('decision-pending', venueStatusData.decisionPendingStatusRows);
  renderTable('camera-ready', venueStatusData.cameraReadyStatusRows);
  renderTable('all-submissions', venueStatusData.submissionStatusRows);

  Webfield2.ui.renderTable('#reviewer-status', venueStatusData.reviewerStatusRows, {
    headings: ['#', 'Reviewer', 'Review Progress', 'Rating <span id="rating-info" class="glyphicon glyphicon-info-sign"></span>', 'Status'],
    renders: [
      function (data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      Handlebars.templates.committeeSummary,
      Handlebars.templates.notesReviewerProgress,
      function (data) {
        return '<table class="table table-condensed table-minimal">'
          .concat(
            "<h4>Average Rating: ".concat(data.averageRating ? data.averageRating.toFixed(2) : '-', "</h4>"),
            "<tbody>"
          )
          .concat(
            Object.entries(data.ratingsMap)
              .map(function (rating) {
                return "<tr><td class='rating'><strong>"
                  .concat(rating[0], ":</strong> ")
                  .concat(rating[1], "</td></tr>");
              })
              .join(""),
            "</tbody></table>"
          );
      },
      Handlebars.templates.notesReviewerStatus,
      function (_) { return null}
    ],
    sortOptions: {
      Reviewer_Name: function(row) { return row.summary.name.toLowerCase(); },
      Papers_Assigned: function(row) { return row.reviewerProgressData.numPapers; },
      Papers_with_Reviews_Missing: function(row) { return row.reviewerProgressData.numPapers - row.reviewerProgressData.numCompletedReviews; },
      Papers_with_Reviews_Submitted: function(row) { return row.reviewerProgressData.numCompletedReviews; },
      Papers_with_Completed_Reviews_Missing: function(row) { return row.reviewerStatusData.numPapers - row.reviewerStatusData.numCompletedReviews; },
      Papers_with_Completed_Reviews: function(row) { return row.reviewerStatusData.numCompletedReviews; },
      Average_Rating: function(row) { return row.ratingData.averageRating; }
    },
    searchProperties: {
      name: ['summary.name'],
      papersAssigned: ['reviewerProgressData.numPapers'],
      averageRating:['ratingData.averageRating'],
      default: ['summary.name'],
      official: ['summary.status.Official'],
      archived: ['summary.status.Archived'],
      volunteer: ['summary.status.Volunteer']
    },
    extraClasses: 'console-table',
    pageSize: 10,
    postRenderTable: function() {
      $('#reviewer-status .console-table th').eq(0).css('width', '4%');  // #
      $('#reviewer-status .console-table th').eq(1).css('width', '23%');  // reviewer
      $('#reviewer-status .console-table th').eq(2).css('width', '33%'); // review progress
      $('#reviewer-status .console-table th').eq(3).css('width', '15%'); // rating
      $('#reviewer-status .console-table th').eq(4).css('width', '25%'); // status
      $('#reviewer-status td.rating').css('white-space', 'nowrap'); // rating no wrap
      $("#rating-info").on("mouseenter", function (e) {
        $(e.target).tooltip({
          title: '<strong class="tooltip-title">Rating map</strong><br/>'.concat(
            Object.entries(REVIEWER_RATING_MAP || {})
              .map(function (item) {
                return "<span>"
                  .concat(item[0], " = ")
                  .concat(item[1], "</span><br/>");
              })
              .join("")
          ),
          html: true,
          placement: "bottom"
        });
      });
    }
  });

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
    extraClasses: 'console-table',
    pageSize: 10
  });

};

main();