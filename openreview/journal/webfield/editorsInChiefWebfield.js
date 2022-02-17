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
var REVIEWERS_NAME = '';
var ACTION_EDITOR_NAME = '';
var ACTION_EDITOR_ID = VENUE_ID + '/' + ACTION_EDITOR_NAME;
var REVIEWERS_ID = VENUE_ID + '/' + REVIEWERS_NAME;
var EDITORS_IN_CHIEF_ID = VENUE_ID + '/' + EDITORS_IN_CHIEF_NAME;

var REVIEWERS_ASSIGNMENT_ID = REVIEWERS_ID + '/-/Assignment';
var REVIEWERS_CONFLICT_ID = REVIEWERS_ID + '/-/Conflict';
var REVIEWERS_AFFINITY_SCORE_ID = REVIEWERS_ID + '/-/Affinity_Score';
var REVIEWERS_CUSTOM_MAX_PAPERS_ID = REVIEWERS_ID + '/-/Custom_Max_Papers';
var REVIEWERS_PENDING_REVIEWS_ID = REVIEWERS_ID + '/-/Pending_Reviews';
var ACTION_EDITORS_ASSIGNMENT_ID = ACTION_EDITOR_ID + '/-/Assignment';
var ACTION_EDITORS_CONFLICT_ID = ACTION_EDITOR_ID + '/-/Conflict';
var ACTION_EDITORS_AFFINITY_SCORE_ID = ACTION_EDITOR_ID + '/-/Affinity_Score';
var ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID = ACTION_EDITOR_ID + '/-/Custom_Max_Papers';
var ACTION_EDITORS_RECOMMENDATION_ID = ACTION_EDITOR_ID + '/-/Recommendation';

var REVIEWER_RATING_MAP = {
  "Exceeds expectations": 3,
  "Meets expectations": 2,
  "Falls below expectations": 1
}

var HEADER = {
  title: SHORT_PHRASE + ' Editors-In-Chief Console',
  instructions: ''
};
var SUBMISSION_GROUP_NAME = 'Paper';
var RECOMMENDATION_NAME = 'Recommendation';
var REVIEW_APPROVAL_NAME = 'Review_Approval';
var REVIEW_NAME = 'Review';
var OFFICIAL_RECOMMENDATION_NAME = 'Official_Recommendation';
var DECISION_NAME = 'Decision';
var DECISION_APPROVAL_NAME = 'Decision_Approval';
var CAMERA_READY_REVISION_NAME = 'Camera_Ready_Revision';
var CAMERA_READY_VERIFICATION_NAME = 'Camera_Ready_Verification';
var UNDER_REVIEW_STATUS = VENUE_ID + '/Under_Review';
var SUBMITTED_STATUS = VENUE_ID + '/Submitted';

var ae_url = '/edges/browse?traverse=' + ACTION_EDITORS_ASSIGNMENT_ID +
'&edit=' + ACTION_EDITORS_ASSIGNMENT_ID + ';' + ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID + ',head:ignore' +
'&browse=' + ACTION_EDITORS_AFFINITY_SCORE_ID +';' + ACTION_EDITORS_RECOMMENDATION_ID + ';' + ACTION_EDITORS_CONFLICT_ID +
'&version=2&referrer=[Editors-In-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + ')';

var reviewers_url = '/edges/browse?traverse=' + REVIEWERS_ASSIGNMENT_ID +
'&edit=' + REVIEWERS_ASSIGNMENT_ID + ';' + REVIEWERS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' +
'&browse=' + REVIEWERS_AFFINITY_SCORE_ID+ ';' + REVIEWERS_CONFLICT_ID + ';' + REVIEWERS_PENDING_REVIEWS_ID + ',head:ignore' +
'&version=2&referrer=[Editors-In-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + ')';

HEADER.instructions = '<ul class="list-inline mb-0"><li><strong>Edge Browser:</strong></li>' +
  '<li><a href="' + ae_url + '">Modify Action Editor Assignments</a></li>' +
  '<li><a href="' + reviewers_url + '">Modify Reviewer Assignments</a></li></ul>';

// Helpers
var getInvitationId = function(number, name, prefix) {
  return Webfield2.utils.getInvitationId(VENUE_ID, number, name, { prefix: prefix, submissionGroupName: SUBMISSION_GROUP_NAME })
};

var getReplies = function(submission, name) {
  return Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, name, { submissionGroupName: SUBMISSION_GROUP_NAME });
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
    tabs: ['Submitted', 'Under Review', 'Decision Approval', 'Camera Ready', 'Submission Complete', 'Action Editor Status', 'Reviewer Status'],
    referrer: args && args.referrer,
    fullWidth: true
  });

  loadData()
    .then(formatData)
    .then(renderData)
    .then(Webfield2.ui.done)
    .fail(Webfield2.ui.errorMessage);
};

var loadData = function() {
  return $.when(
    Webfield2.api.getGroupsByNumber(VENUE_ID, ACTION_EDITOR_NAME),
    Webfield2.api.getGroupsByNumber(VENUE_ID, REVIEWERS_NAME, { withProfiles: true}),
    Webfield2.api.getAllSubmissions(SUBMISSION_ID),
    Webfield2.api.getGroup(VENUE_ID + '/' + ACTION_EDITOR_NAME, { withProfiles: true}),
    Webfield2.api.getGroup(VENUE_ID + '/' + REVIEWERS_NAME, { withProfiles: true}),
    Webfield2.api.getAll('/invitations', {
      regex: VENUE_ID + '/' + SUBMISSION_GROUP_NAME,
      type: 'all',
      select: 'id,cdate,duedate,expdate',
      // expired: true
    }).then(function(invitations) {
      return _.keyBy(invitations, 'id');
    }),
    Webfield2.api.getAll('/edges', {
      invitation: VENUE_ID + '/' + ACTION_EDITOR_NAME + '/-/' + RECOMMENDATION_NAME,
      groupBy: 'head'
    }),
    Webfield2.api.getAssignedInvitations(VENUE_ID, EDITORS_IN_CHIEF_NAME),
  );
};

var formatData = function(aeByNumber, reviewersByNumber, submissions, actionEditors, reviewers, invitationsById, actionEditorRecommendations, invitations) {
  var referrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + EDITORS_IN_CHIEF_ID + '#paper-status)');

  // build the rows
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
      ratingData: {
        ratings:[],
        ratingsMap: {
          "Exceeds expectations": 0,
          "Meets expectations": 0,
          "Falls below expectations": 0
        },
        averageRating: 0
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

    // Build array of tasks
    var tasks = [];
    // Review approval by AE
    var reviewApprovalInvitation = invitationsById[getInvitationId(number, REVIEW_APPROVAL_NAME)];
    var reviewApprovalNotes = getReplies(submission, REVIEW_APPROVAL_NAME);
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

    if (reviewApprovalInvitation) {
      tasks.push({
        id: reviewApprovalInvitation.id,
        startdate: reviewApprovalInvitation.cdate,
        duedate: reviewApprovalInvitation.duedate,
        complete: reviewApprovalNotes.length > 0,
        replies: reviewApprovalNotes
      });
    }

    if (reviewInvitation) {
      tasks.push({
        id: reviewInvitation.id,
        startdate: reviewInvitation.cdate,
        duedate: reviewInvitation.duedate,
        complete: reviewNotes.length >= 3,
        replies: reviewNotes
      });
    }

    if (officialRecommendationInvitation) {
      tasks.push({
        id: officialRecommendationInvitation.id,
        startdate: officialRecommendationInvitation.cdate,
        duedate: officialRecommendationInvitation.duedate,
        complete: officialRecommendationNotes.length >= 3,
        replies: officialRecommendationNotes
      });
    }

    if (reviewerRatingInvitations.length) {
      tasks.push({
        id: getInvitationId(number, 'Reviewer_Rating'),
        startdate: reviewerRatingInvitations[0].cdate,
        duedate: reviewerRatingInvitations[0].duedate,
        complete: reviewerRatingReplies.length == reviewNotes.length,
        replies: reviewerRatingReplies
      });
    }

    if (decisionInvitation) {
      tasks.push({
        id: decisionInvitation.id,
        startdate: decisionInvitation.cdate,
        duedate: decisionInvitation.duedate,
        complete: decisionNotes.length > 0,
        replies: decisionNotes
      });
    }

    if (decisionApprovalInvitation) {
      tasks.push({
        id: decisionApprovalInvitation.id,
        startdate: decisionApprovalInvitation.cdate,
        duedate: decisionApprovalInvitation.duedate,
        complete: decisionApprovalNotes.length > 0,
        replies: decisionApprovalNotes
      });
    }

    if (cameraReadyRevisionInvitation) {
      var complete = submission.invitations.includes(cameraReadyRevisionInvitation.id);
      cameraReadyTask = {
        id: cameraReadyRevisionInvitation.id,
        startdate: cameraReadyRevisionInvitation.cdate,
        duedate: cameraReadyRevisionInvitation.duedate,
        complete: complete,
        replies: complete ? [1] : []
      };
      tasks.push(cameraReadyTask);
    }

    if (cameraReadyVerificationInvitation) {
      cameraReadyVerificationTask = {
        id: cameraReadyVerificationInvitation.id,
        startdate: cameraReadyVerificationInvitation.cdate,
        duedate: cameraReadyVerificationInvitation.duedate,
        complete: cameraReadyVerificationNotes.length > 0,
        replies: cameraReadyVerificationNotes
      };
      tasks.push(cameraReadyVerificationTask);
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
      var reviewerRecommendation = null;
      var status = {};
      var reviewerStatus = reviewerStatusById[reviewer.id];

      if (completedReview) {
        reviewerRecommendation = recommendationByReviewer[completedReview.signatures[0]];
        status = {};
        if (reviewerRecommendation) {
          status.Recommendation = reviewerRecommendation.content.decision_recommendation.value;
          status.Certifications = reviewerRecommendation.content.certification_recommendations ? reviewerRecommendation.content.certification_recommendations.value.join(', ') : '';
        }
        var reviewerRating = reviewerRatingReplies.find(function (p) {
          return p.replyto === completedReview.id;
        });
        if(reviewerRating){
          status.Rating = reviewerRating.content.rating.value
          if(reviewerStatus){
            var rating = reviewerRating.content.rating.value;
            var ratingValue = REVIEWER_RATING_MAP[rating];
            reviewerStatus.ratingData.ratings.push(rating);
            reviewerStatus.ratingData.ratingsMap[rating] += 1;
            var count = reviewerStatus.ratingData.ratings.length;
            if (count > 1) {
              reviewerStatus.ratingData.averageRating = (reviewerStatus.ratingData.averageRating * (count - 1) + ratingValue) / count;
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
        forumUrl: 'https://openreview.net/forum?' + $.param({
          id: submission.id,
          noteId: submission.id,
          invitationId: getInvitationId(submission.number, REVIEW_NAME)
        })
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


    paperActionEditors.forEach(function(actionEditor, number) {
      var completedDecision = decisions.find(function(decision) { return decision.signatures[0] == VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/Action_Editors'; });
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
    var decision = decisions.length && decisions[0];
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
        referrer: referrerUrl,
        actions: [UNDER_REVIEW_STATUS].includes(submission.content.venueid.value) ? [
          {
            name: 'Edit Assignments',
            url: '/edges/browse?start=staticList,type:head,ids:' + submission.id +
            '&traverse='+ REVIEWERS_ASSIGNMENT_ID +
            '&edit='+ REVIEWERS_ASSIGNMENT_ID + ';' + REVIEWERS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' +
            '&browse=' + REVIEWERS_AFFINITY_SCORE_ID + ';' + REVIEWERS_CONFLICT_ID + ';' + REVIEWERS_PENDING_REVIEWS_ID + ',head:ignore' +
            '&version=2'
          }
        ] : []
      },
      actionEditorProgressData: {
        recommendation: metaReview && metaReview.content.recommendation,
        status: {
          Certification: metaReview ? metaReview.content.certification.join(', ') : ''
        },
        numMetaReview: metaReview ? 'One' : 'No',
        areachair: !actionEditor.name ? { name: 'No Action Editor' } : { name: actionEditor.name, email: actionEditor.email },
        actionEditor: actionEditor,
        metaReview: metaReview,
        referrer: referrerUrl,
        decisionApprovalPending: metaReview && decisionApprovalNotes.length == 0,
        cameraReadyPending: (cameraReadyTask && !cameraReadyTask.complete) || (cameraReadyVerificationTask && !cameraReadyVerificationTask.complete),
        metaReviewName: 'Decision',
        committeeName: 'Action Editor',
        actions: [UNDER_REVIEW_STATUS, SUBMITTED_STATUS].includes(submission.content.venueid.value) ? [
          {
            name: 'Edit Assignments',
            url: '/edges/browse?start=staticList,type:head,ids:' + submission.id +
            '&traverse=' + ACTION_EDITORS_ASSIGNMENT_ID +
            '&edit=' + ACTION_EDITORS_ASSIGNMENT_ID + ';' + ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID + ',head:ignore' +
            '&browse=' + ACTION_EDITORS_AFFINITY_SCORE_ID + ';' + ACTION_EDITORS_RECOMMENDATION_ID + ';' + ACTION_EDITORS_CONFLICT_ID +
            '&version=2'
          }
        ] : [],
        tableWidth: '100%'
      },
      tasks: { invitations: tasks, forumId: submission.id },
      status: submission.content.venue.value
    });
  });

  return {
    submissionStatusRows: paperStatusRows.filter(function(row) { return row.submission.content.venueid === SUBMITTED_STATUS; }),
    paperStatusRows: paperStatusRows.filter(function(row) { return row.submission.content.venueid === UNDER_REVIEW_STATUS && !row.actionEditorProgressData.decisionApprovalPending && !row.actionEditorProgressData.cameraReadyPending;  }),
    decisionApprovalStatusRows: paperStatusRows.filter(function(row) { return row.submission.content.venueid === UNDER_REVIEW_STATUS && row.actionEditorProgressData.decisionApprovalPending; }),
    cameraReadyStatusRows: paperStatusRows.filter(function(row) { return row.submission.content.venueid === UNDER_REVIEW_STATUS && row.actionEditorProgressData.cameraReadyPending; }),
    completeSubmissionStatusRows: paperStatusRows.filter(function(row) { return ![SUBMITTED_STATUS, UNDER_REVIEW_STATUS].includes(row.submission.content.venueid); }),
    reviewerStatusRows: Object.values(reviewerStatusById),
    actionEditorStatusRows: Object.values(actionEditorStatusById),
    invitations: invitations
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
          referrer: encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + ')')
        });
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
      numRecommendationsDone: ['reviewProgressData.numSubmittedRecommendations'],
      decision: ['actionEditorProgressData.recommendation'],
      status: ['status'],
      default: ['submissionNumber.number', 'submission.content.title']
    },
    reminderOptions: {
      container: 'a.send-reminder-link',
      defaultSubject: SHORT_PHRASE + ' Reminder',
      defaultBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the submission page:\n\n{{forumUrl}}\n\n' +
        'Thank you,\n' + SHORT_PHRASE + ' Editor-in-Chief',
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
    postRenderTable: function() {
      $('#' + container + ' .console-table th').eq(0).css('width', '2%');  // [ ]
      $('#' + container + ' .console-table th').eq(1).css('width', '3%');  // #
      $('#' + container + ' .console-table th').eq(2).css('width', '20%'); // Paper Summary
      $('#' + container + ' .console-table th').eq(3).css('width', '22%'); // Review Progress
      $('#' + container + ' .console-table th').eq(4).css('width', '22%'); // Action Editor Decision
      $('#' + container + ' .console-table th').eq(5).css('width', '20%'); // Tasks
      $('#' + container + ' .console-table th').eq(6).css('width', '11%'); // Status
    }
  });
};

var renderData = function(venueStatusData) {
  renderTable('submitted', venueStatusData.submissionStatusRows);
  renderTable('under-review', venueStatusData.paperStatusRows);
  renderTable('decision-approval', venueStatusData.decisionApprovalStatusRows);
  renderTable('camera-ready', venueStatusData.cameraReadyStatusRows);
  renderTable('submission-complete', venueStatusData.completeSubmissionStatusRows);

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
            "<h4>Average Rating: ".concat(data.averageRating.toFixed(2), "</h4>"),
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
      Handlebars.templates.notesReviewerStatus
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
    },
    extraClasses: 'console-table',
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
    extraClasses: 'console-table'
  });

};

main();
