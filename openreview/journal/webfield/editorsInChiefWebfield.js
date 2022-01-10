// webfield_template
// Remove line above if you don't want this page to be overwriten

/* globals $: false */
/* globals view: false */
/* globals Handlebars: false */
/* globals Webfield2: false */

// Constants
var VENUE_ID = '.TMLR';
var SHORT_PHRASE = 'TMLR';
var SUBMISSION_ID = '.TMLR/-/Author_Submission';
var EDITORS_IN_CHIEF_NAME = 'Editors_In_Chief';
var REVIEWERS_NAME = 'Reviewers';
var ACTION_EDITOR_NAME = 'Action_Editors';
var EDITORS_IN_CHIEF_ID = VENUE_ID + '/' + EDITORS_IN_CHIEF_NAME;
var HEADER = {
  title: 'TMLR Editors-in-Chief Console',
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
var SUBMITTED_STATUS = '.TMLR/Submitted';
var UNDER_REVIEW_STATUS = '.TMLR/Under_Review';

var ae_url = '/edges/browse?traverse=.TMLR/Action_Editors/-/Assignment&edit=.TMLR/Action_Editors/-/Assignment;.TMLR/Action_Editors/-/Custom_Max_Papers,head:ignore&browse=.TMLR/Action_Editors/-/Affinity_Score;.TMLR/Action_Editors/-/Recommendation;.TMLR/Action_Editors/-/Conflict&version=2&referrer=[Editors-in-Chief Console](/group?id=.TMLR/Editors_In_Chief)';
var reviewers_url = '/edges/browse?traverse=.TMLR/Reviewers/-/Assignment&edit=.TMLR/Reviewers/-/Assignment;.TMLR/Reviewers/-/Custom_Max_Papers,head:ignore&browse=.TMLR/Reviewers/-/Affinity_Score;.TMLR/Reviewers/-/Conflict;.TMLR/Reviewers/-/Pending_Reviews,head:ignore&version=2&referrer=[Editors-in-Chief Console](/group?id=.TMLR/Editors_In_Chief)';

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

// Main function is the entry point to the webfield code
var main = function() {
  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Submitted', 'Under Review', 'Decision Approval', 'Submission Complete', 'Action Editor Status', 'Reviewer Status', 'Editors-in-Chief Tasks'],
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
      tasks.push({
        id: cameraReadyRevisionInvitation.id,
        startdate: cameraReadyRevisionInvitation.cdate,
        duedate: cameraReadyRevisionInvitation.duedate,
        complete: submission.invitations.includes(cameraReadyRevisionInvitation.id),
        replies: []
      });
    }

    if (cameraReadyVerificationInvitation) {
      tasks.push({
        id: cameraReadyVerificationInvitation.id,
        startdate: cameraReadyVerificationInvitation.cdate,
        duedate: cameraReadyVerificationInvitation.duedate,
        complete: cameraReadyVerificationNotes.length > 0,
        replies: cameraReadyVerificationNotes
      });
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
        name: reviewer.name,
        email: reviewer.email,
        completedReview: completedReview && true,
        forum: submission.id,
        note: completedReview && completedReview.id,
        status: status,
        forumUrl: 'https://openreview.net/forum?' + $.param({
          id: submission.id,
          noteId: submission.id,
          invitationId: getInvitationId(submission.number, REVIEW_NAME)
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
        actions: ['.TMLR/Under_Review'].includes(submission.content.venueid.value) ? [
          {
            name: 'Edit Assignments',
            url: '/edges/browse?start=staticList,type:head,ids:' + submission.id + '&traverse=.TMLR/Reviewers/-/Assignment&edit=.TMLR/Reviewers/-/Assignment;.TMLR/Reviewers/-/Custom_Max_Papers,head:ignore;&browse=.TMLR/Reviewers/-/Affinity_Score;.TMLR/Reviewers/-/Conflict;.TMLR/Reviewers/-/Pending_Reviews,head:ignore&version=2'
          },
          {
            name: 'Edit Review Invitation',
            url: '/invitation/edit?id=' + getInvitationId(number, REVIEW_NAME)
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
        metaReviewName: 'Decision',
        committeeName: 'Action Editor',
        actions: ['.TMLR/Under_Review', '.TMLR/Submitted'].includes(submission.content.venueid.value) ? [
          {
            name: 'Edit Assignments',
            url: '/edges/browse?start=staticList,type:head,ids:' + submission.id + '&traverse=.TMLR/Action_Editors/-/Assignment&edit=.TMLR/Action_Editors/-/Assignment;.TMLR/Action_Editors/-/Custom_Max_Papers,head:ignore&browse=.TMLR/Action_Editors/-/Affinity_Score;.TMLR/Action_Editors/-/Recommendation;.TMLR/Action_Editors/-/Conflict&version=2'
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
    paperStatusRows: paperStatusRows.filter(function(row) { return row.submission.content.venueid === UNDER_REVIEW_STATUS; }),
    decisionApprovalStatusRows: paperStatusRows.filter(function(row) { return row.submission.content.venueid === UNDER_REVIEW_STATUS && row.actionEditorProgressData.decisionApprovalPending; }),
    completeSubmissionStatusRows: paperStatusRows.filter(function(row) { return ![SUBMITTED_STATUS, UNDER_REVIEW_STATUS].includes(row.submission.content.venueid); }),
    reviewerStatusRows: Object.values(reviewerStatusById),
    actionEditorStatusRows: Object.values(actionEditorStatusById),
    invitations: invitations
  };
};

// Render functions
var renderTable = function(container, rows) {
  Webfield2.ui.renderTable('#' + container, rows, {
    headings: ['#', 'Paper Summary', 'Review Progress', 'Action Editor Decision', 'Tasks', 'Status'],
    renders: [
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
      decision: ['actionEditorProgressData.recommendation'],
      status: ['status'],
      default: ['submissionNumber.number', 'submission.content.title']
    },
    reminderOptions: {
      container: 'a.send-reminder-link',
      defaultSubject: SHORT_PHRASE + ' Reminder',
      defaultBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the review page:\n\n{{submit_review_link}}\n\n' +
        'Thank you,\n' + SHORT_PHRASE + ' Editor-in-Chief'
    },
    extraClasses: 'console-table paper-table',
    postRenderTable: function() {
      $('#' + container + ' .console-table th').eq(0).css('width', '3%');  // #
      $('#' + container + ' .console-table th').eq(1).css('width', '21%'); // Paper Summary
      $('#' + container + ' .console-table th').eq(2).css('width', '22%'); // Review Progress
      $('#' + container + ' .console-table th').eq(3).css('width', '22%'); // Action Editor Decision
      $('#' + container + ' .console-table th').eq(4).css('width', '20%'); // Tasks
      $('#' + container + ' .console-table th').eq(5).css('width', '12%'); // Status
    }
  });
};

var renderData = function(venueStatusData) {
  renderTable('submitted', venueStatusData.submissionStatusRows);
  renderTable('under-review', venueStatusData.paperStatusRows);
  renderTable('decision-approval', venueStatusData.decisionApprovalStatusRows);
  renderTable('submission-complete', venueStatusData.completeSubmissionStatusRows);

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

  Webfield2.ui.renderTasks(
    '#editors-in-chief-tasks',
    venueStatusData.invitations,
    { referrer: encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + '#editors-in-chief-tasks)') }
  );
};

main();
