// webfield_template
// Remove line above if you don't want this page to be overwriten

/* globals $: false */
/* globals view: false */
/* globals Handlebars: false */
/* globals Webfield2: false */

// Editors-in-Chief console, paginated.
//
// The original console loads every submission, every per-paper group and every
// per-paper invitation up front and does all filtering in the browser. That is
// O(venue size) on every page load and stops being viable somewhere in the low
// thousands of submissions.
//
// This version never loads the whole venue. Landing on a tab, or paging within
// one, issues a bounded set of requests for just that page:
//
//   1. one /notes request  - the page of submissions for the tab's venueid set,
//      carrying only the reply fields the rows read
//   2. one /invitations request per paper - the task invitations and the
//      per-reviewer Rating invitations
//   3. one /groups request per paper - the reviewer and action editor groups
//      together with their anonymous groups
//   4. one /profiles/search - names and emails for the members just fetched
//
// The cost of a page is a function of PAGE_SIZE, not of the size of the venue,
// so the console behaves the same on a journal with 500 submissions and one
// with 500,000.

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
var REVIEWERS_REPORT_ID = REVIEWERS_ID + '/-/Reviewer_Report';
var ACTION_EDITORS_ASSIGNMENT_ID = ACTION_EDITOR_ID + '/-/Assignment';
var ACTION_EDITORS_ARCHIVED_ASSIGNMENT_ID = ACTION_EDITOR_ID + '/-/Archived_Assignment';
var ACTION_EDITORS_CONFLICT_ID = ACTION_EDITOR_ID + '/-/Conflict';
var ACTION_EDITORS_AFFINITY_SCORE_ID = ACTION_EDITOR_ID + '/-/Affinity_Score';
var ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID = ACTION_EDITOR_ID + '/-/Custom_Max_Papers';
var ACTION_EDITORS_RECOMMENDATION_ID = ACTION_EDITOR_ID + '/-/Recommendation';
var ACTION_EDITORS_AVAILABILITY_ID = ACTION_EDITOR_ID + '/-/' + AVAILABILITY_NAME;

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
var RETRACTION_APPROVAL_NAME = 'Retraction_Approval';

var UNDER_REVIEW_STATUS = VENUE_ID + '/Under_Review';
var SUBMITTED_STATUS = VENUE_ID + '/Submitted';
var ASSIGNING_AE_STATUS = VENUE_ID + '/Assigning_AE';
var ASSIGNED_AE_STATUS = VENUE_ID + '/Assigned_AE';
var WITHDRAWN_STATUS = VENUE_ID + '/Withdrawn_Submission';
var RETRACTED_STATUS = VENUE_ID + '/Retracted_Acceptance';
var REJECTED_STATUS = VENUE_ID + '/Rejected';
var DESK_REJECTED_STATUS = VENUE_ID + '/Desk_Rejected';
var DECISION_PENDING_STATUS = VENUE_ID + '/Decision_Pending';

var PAGE_SIZE = 25;

var referrerUrl = encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + ')');
var rowReferrerUrl = encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + '#paper-status)');

// ---------------------------------------------------------------------------
// Tabs
//
// Each submission tab is a server-side query: a set of venueids, paged and
// sorted by the API. Membership is exact and the total count is whatever the
// API reports, with no need to hold the venue in memory.
//
// The original console further split Under_Review into three tabs (review /
// discussion / decision) using state derived in the browser from the replies
// and invitations of every submission. That predicate does not exist on the
// server, so it cannot be paged. Here those papers live in one tab and the
// derived state is shown per row in the Pending column instead. If the journal
// ever materializes that state - a tag or content field maintained by the
// existing process functions - each split becomes another entry in this list
// with its own venueid or content filter, and nothing else has to change.
// ---------------------------------------------------------------------------
var SUBMISSION_TABS = [
  { id: 'submitted', label: 'Submitted', venueids: [SUBMITTED_STATUS, ASSIGNING_AE_STATUS, ASSIGNED_AE_STATUS] },
  { id: 'under-review', label: 'Under Review', venueids: [UNDER_REVIEW_STATUS] },
  { id: 'decision-pending', label: 'Decision Pending', venueids: [DECISION_PENDING_STATUS] },
  { id: 'accepted', label: 'Accepted', venueids: [VENUE_ID] },
  { id: 'rejected', label: 'Rejected', venueids: [REJECTED_STATUS, DESK_REJECTED_STATUS] },
  { id: 'withdrawn-retracted', label: 'Withdrawn Retracted', venueids: [WITHDRAWN_STATUS, RETRACTED_STATUS] },
  { id: 'all-submissions', label: 'All Submissions', venueids: null }
];

var SORT_OPTIONS = [
  { label: 'Paper number (newest first)', value: 'number:desc' },
  { label: 'Paper number (oldest first)', value: 'number:asc' },
  { label: 'Submission date (newest first)', value: 'cdate:desc' },
  { label: 'Submission date (oldest first)', value: 'cdate:asc' },
  { label: 'Last activity', value: 'tmdate:desc' }
];

// Only the fields the rows read. details=replies otherwise returns every reply
// in full, including review bodies, which dominate the payload.
//
// Two behaviours of the API's select matter here: a select that omits the
// details.replies[*] entries drops details.replies silently, and content is
// omitted from a reply entirely when none of the selected content fields exist
// on it, so every reply content read below is null-safe.
var SUBMISSION_SELECT = [
  'id', 'forum', 'number', 'cdate', 'mdate', 'tcdate', 'tmdate', 'invitations', 'content',
  'details.replies[*].id',
  'details.replies[*].forum',
  'details.replies[*].replyto',
  'details.replies[*].tcdate',
  'details.replies[*].invitations',
  'details.replies[*].signatures',
  'details.replies[*].readers',
  'details.replies[*].content.rating',
  'details.replies[*].content.recommendation',
  'details.replies[*].content.certifications',
  'details.replies[*].content.decision_recommendation',
  'details.replies[*].content.certification_recommendations',
  'details.replies[*].content.comment',
  'details.replies[*].content.title'
].join(',');

var HEADER = {
  title: SHORT_PHRASE + ' Editors-in-Chief Console',
  instructions: ''
};

var ae_url = '/edges/browse?traverse=' + ACTION_EDITORS_ASSIGNMENT_ID +
  '&edit=' + ACTION_EDITORS_ASSIGNMENT_ID + ';' + ACTION_EDITORS_CUSTOM_MAX_PAPERS_ID + ',head:ignore' + ';' + ACTION_EDITORS_AVAILABILITY_ID + ',head:ignore' +
  '&browse=' + ACTION_EDITORS_ARCHIVED_ASSIGNMENT_ID + ';' + ACTION_EDITORS_AFFINITY_SCORE_ID + ';' + ACTION_EDITORS_RECOMMENDATION_ID + ';' + ACTION_EDITORS_CONFLICT_ID +
  '&version=2&referrer=' + referrerUrl;
var reviewers_url = '/edges/browse?traverse=' + REVIEWERS_ASSIGNMENT_ID +
  '&edit=' + REVIEWERS_ASSIGNMENT_ID + ';' + REVIEWERS_INVITE_ASSIGNMENT_ID + ';' + REVIEWERS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' + REVIEWERS_AVAILABILITY_ID + ',head:ignore' +
  '&browse=' + REVIEWERS_ARCHIVED_ASSIGNMENT_ID + ';' + REVIEWERS_AFFINITY_SCORE_ID + ';' + REVIEWERS_CONFLICT_ID + ';' + REVIEWERS_PENDING_REVIEWS_ID + ',head:ignore;' +
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
var getInvitationId = function(number, name, prefix) {
  return Webfield2.utils.getInvitationId(VENUE_ID, number, name, { prefix: prefix, submissionGroupName: SUBMISSION_GROUP_NAME });
};

var getReplies = function(submission, name, prefix) {
  return Webfield2.utils.getRepliesfromSubmission(VENUE_ID, submission, name, { prefix: prefix, submissionGroupName: SUBMISSION_GROUP_NAME });
};

var paperPrefix = function(number) {
  return VENUE_ID + '/' + SUBMISSION_GROUP_NAME + number + '/';
};

var updateEarlyLateTaskDuedate = function(earlylateTaskDueDate, task) {
  if ((earlylateTaskDueDate === 0 || earlylateTaskDueDate > task.duedate) && !task.complete) {
    return task.duedate;
  }
  return earlylateTaskDueDate;
};

var profileInfo = function(profile, fallbackId) {
  if (!profile) {
    return {
      id: fallbackId,
      name: fallbackId.indexOf('~') === 0 ? view.prettyId(fallbackId) : fallbackId,
      email: fallbackId
    };
  }
  var nameEntry = _.find(profile.content.names, ['preferred', true]) || _.first(profile.content.names) || {};
  return {
    id: profile.id,
    name: nameEntry.fullname || profile.id,
    email: profile.content.preferredEmail || (profile.content.emailsConfirmed || [])[0]
  };
};

// ---------------------------------------------------------------------------
// Page loading
//
// Everything below fetches for a bounded set of paper numbers. Nothing here
// scales with the size of the venue.
// ---------------------------------------------------------------------------

// One /notes request for the page. count comes back because both offset and
// limit are set, which is what drives the pagination control.
var loadSubmissionPage = function(tab, pageNumber, state) {
  var query = {
    invitation: SUBMISSION_ID,
    domain: VENUE_ID,
    details: 'replies',
    select: SUBMISSION_SELECT,
    sort: state.sort,
    limit: PAGE_SIZE,
    offset: (pageNumber - 1) * PAGE_SIZE
  };
  if (tab.venueids) {
    query['content.venueid'] = tab.venueids.join(',');
  }
  if (state.filterNumber) {
    query.number = state.filterNumber;
  }
  return Webfield2.api.get('/notes', query).then(function(result) {
    var submissions = result.notes || [];
    // A selected request omits details for a submission with no replies, where
    // an unselected one returns details.replies: []. Normalize it back so the
    // reply helpers here and in Webfield2.utils can assume the array exists.
    submissions.forEach(function(submission) {
      if (!submission.details) {
        submission.details = {};
      }
      if (!submission.details.replies) {
        submission.details.replies = [];
      }
    });
    return { submissions: submissions, count: result.count || submissions.length };
  });
};

// One /invitations request per paper.
//
// An earlier version addressed the task invitations by id and scanned each
// paper's prefix separately for the per-reviewer Rating invitations, whose
// anonymous ids are not knowable in advance. The prefix scan already returns
// everything the id lookup did, so the id path was redundant: this is one
// request per paper instead of two plus id chunking, and there is no query
// string length to worry about.
//
// /invitations takes a single prefix, so a page costs one request per paper.
// They are small and run in parallel, and the count is bounded by PAGE_SIZE
// rather than by the venue. A multi-prefix or id-list capability on the
// endpoint would collapse these into one request.
var loadPageInvitations = function(numbers) {
  if (!numbers.length) {
    return $.Deferred().resolve({ invitationsById: {}, ratingsByNumber: {} }).promise();
  }
  var requests = numbers.map(function(number) {
    return Webfield2.api.get('/invitations', {
      prefix: paperPrefix(number),
      type: 'all',
      select: 'id,cdate,duedate,expdate',
      domain: VENUE_ID
    }).then(function(result) {
      return result.invitations || [];
    });
  });

  return $.when.apply($, requests).then(function() {
    var invitationsById = {};
    var ratingsByNumber = {};
    Array.prototype.slice.call(arguments).forEach(function(invitations, index) {
      var ratings = [];
      (invitations || []).forEach(function(invitation) {
        invitationsById[invitation.id] = invitation;
        if (invitation.id.endsWith('/-/Rating')) {
          ratings.push(invitation);
        }
      });
      ratingsByNumber[numbers[index]] = ratings;
    });
    return { invitationsById: invitationsById, ratingsByNumber: ratingsByNumber };
  });
};

// One /groups request per paper, then a single /profiles/search for every
// member the page turned up.
var loadPageGroups = function(numbers) {
  if (!numbers.length) {
    return $.Deferred().resolve({ reviewersByNumber: {}, aeByNumber: {} }).promise();
  }
  var reviewerAnonName = REVIEWERS_NAME.slice(0, -1) + '_';
  var aeAnonName = ACTION_EDITOR_NAME.slice(0, -1) + '_';

  var requests = numbers.map(function(number) {
    return Webfield2.api.get('/groups', {
      prefix: paperPrefix(number),
      select: 'id,members',
      domain: VENUE_ID
    }).then(function(result) {
      return result.groups || [];
    });
  });

  return $.when.apply($, requests).then(function() {
    var groupsByNumber = {};
    Array.prototype.slice.call(arguments).forEach(function(groups, index) {
      groupsByNumber[numbers[index]] = groups || [];
    });

    // Resolve each role's members to their anonymous group before asking for
    // profiles. A per-paper role group lists anonymous group ids rather than
    // profile ids - TMLR/Paper1/Reviewers holds TMLR/Paper1/Reviewer_LhXv, not
    // ~David_Belanger1 - so the anonymous groups have to be indexed under both
    // their own id and their member, and the profile id is only known after
    // that lookup.
    var resolveRole = function(groups, roleName, anonRoleName, number) {
      var roleGroup = groups.find(function(group) {
        return group.id === paperPrefix(number) + roleName;
      });
      if (!roleGroup) {
        return [];
      }
      var anonByKey = {};
      groups.forEach(function(group) {
        if (group.id.indexOf(paperPrefix(number) + anonRoleName) === 0) {
          anonByKey[group.id] = group;
          if ((group.members || []).length) {
            anonByKey[group.members[0]] = group;
          }
        }
      });
      return (roleGroup.members || []).map(function(member) {
        var anonGroup = anonByKey[member];
        return {
          member: member,
          anonGroup: anonGroup,
          id: anonGroup && (anonGroup.members || []).length ? anonGroup.members[0] : member,
          anonId: anonGroup ? anonGroup.id.split(anonRoleName)[1] : null,
          anonymousGroupId: anonGroup ? anonGroup.id : null
        };
      });
    };

    var resolved = {};
    var memberIdSet = new Set();
    numbers.forEach(function(number) {
      var groups = groupsByNumber[number] || [];
      resolved[number] = {
        reviewers: resolveRole(groups, REVIEWERS_NAME, reviewerAnonName, number),
        actionEditors: resolveRole(groups, ACTION_EDITOR_NAME, aeAnonName, number)
      };
      resolved[number].reviewers.concat(resolved[number].actionEditors).forEach(function(entry) {
        if (entry.id.indexOf('~') === 0 || entry.id.indexOf('@') > -1) {
          memberIdSet.add(entry.id);
        }
      });
    });

    var profilesP = memberIdSet.size
      ? Webfield2.api.post('/profiles/search', { ids: Array.from(memberIdSet) })
      : $.Deferred().resolve({ profiles: [] }).promise();

    return profilesP.then(function(result) {
      var profilesById = _.keyBy(result.profiles || [], 'id');
      var withProfile = function(entries) {
        return entries.map(function(entry) {
          var info = profileInfo(profilesById[entry.id], entry.id);
          return {
            id: entry.id,
            anonId: entry.anonId,
            anonymousGroupId: entry.anonymousGroupId,
            name: info.name,
            email: info.email
          };
        });
      };
      var reviewersByNumber = {};
      var aeByNumber = {};
      numbers.forEach(function(number) {
        reviewersByNumber[number] = withProfile(resolved[number].reviewers);
        aeByNumber[number] = withProfile(resolved[number].actionEditors);
      });
      return { reviewersByNumber: reviewersByNumber, aeByNumber: aeByNumber };
    });
  });
};

// AE recommendation counts.
//
// This is the one request that is not scoped to the page. /edges takes a single
// `head`, and the repository only ever sets the `heads` ($in) form on an
// internal permissions path, so a page's heads cannot be asked for together.
// The grouped response is one {head, count} pair per submission with a
// recommendation, so it is small in absolute terms; it is fetched once on the
// first page that needs it and reused for the life of the console. Teaching
// /edges to accept a head list, the way /invitations already accepts `ids`,
// would make this page-scoped like everything else.
var recommendationCountsP = null;

var loadRecommendationCounts = function() {
  if (!recommendationCountsP) {
    recommendationCountsP = Webfield2.api.get('/edges', {
      invitation: ACTION_EDITORS_RECOMMENDATION_ID,
      groupBy: 'head',
      select: 'count',
      domain: VENUE_ID
    }).then(function(response) {
      var counts = {};
      (response.groupedEdges || []).forEach(function(group) {
        counts[group.id.head] = group.count;
      });
      return counts;
    }, function() {
      // Recommendation counts are decoration. A failure here must not take the
      // whole page down with it, and must not poison the cache.
      recommendationCountsP = null;
      return {};
    });
  }
  return recommendationCountsP;
};

// ---------------------------------------------------------------------------
// Row building
// ---------------------------------------------------------------------------
var buildTasks = function(submission, invitationsById, ratingInvitations, reviewers, recommendationCount) {
  var number = submission.number;
  var tasks = [];
  var earlylateTaskDueDate = 0;

  var push = function(invitation, complete, replies) {
    if (!invitation) {
      return;
    }
    var task = {
      id: invitation.id,
      cdate: invitation.cdate,
      duedate: invitation.duedate,
      complete: complete,
      replies: replies || []
    };
    earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, task);
    tasks.push(task);
  };

  var reviewApprovalNotes = getReplies(submission, REVIEW_APPROVAL_NAME);
  var deskRejectionApprovalNotes = getReplies(submission, DESK_REJECTION_APPROVAL_NAME);
  var reviewNotes = getReplies(submission, REVIEW_NAME);
  var officialRecommendationNotes = getReplies(submission, OFFICIAL_RECOMMENDATION_NAME);
  var decisionNotes = getReplies(submission, DECISION_NAME);
  var decisionApprovalNotes = getReplies(submission, DECISION_APPROVAL_NAME);
  var cameraReadyVerificationNotes = getReplies(submission, CAMERA_READY_VERIFICATION_NAME);
  var retractionApprovalNotes = getReplies(submission, RETRACTION_APPROVAL_NAME);
  var ratingReplies = submission.details.replies.filter(function(reply) {
    return reply.invitations[0].indexOf('/-/Rating') > -1;
  });

  push(invitationsById[getInvitationId(number, RECOMMENDATION_NAME, ACTION_EDITOR_NAME)],
    recommendationCount >= NUMBER_OF_REVIEWERS, Array(recommendationCount).fill(1));
  push(invitationsById[getInvitationId(number, REVIEW_APPROVAL_NAME)],
    reviewApprovalNotes.length > 0, reviewApprovalNotes);
  push(invitationsById[getInvitationId(number, DESK_REJECTION_APPROVAL_NAME)],
    deskRejectionApprovalNotes.length > 0, deskRejectionApprovalNotes);
  push(invitationsById[getInvitationId(number, 'Assignment', REVIEWERS_NAME)],
    reviewers.length >= NUMBER_OF_REVIEWERS, reviewers);
  push(invitationsById[getInvitationId(number, REVIEW_NAME)],
    reviewNotes.length >= NUMBER_OF_REVIEWERS, reviewNotes);
  push(invitationsById[getInvitationId(number, OFFICIAL_RECOMMENDATION_NAME)],
    officialRecommendationNotes.length >= NUMBER_OF_REVIEWERS, officialRecommendationNotes);

  if (ratingInvitations.length) {
    var ratingTask = {
      id: getInvitationId(number, 'Reviewer_Rating'),
      cdate: ratingInvitations[0].cdate,
      duedate: ratingInvitations[0].duedate,
      complete: ratingReplies.length === reviewNotes.length,
      replies: ratingReplies
    };
    earlylateTaskDueDate = updateEarlyLateTaskDuedate(earlylateTaskDueDate, ratingTask);
    tasks.push(ratingTask);
  }

  push(invitationsById[getInvitationId(number, DECISION_NAME)],
    decisionNotes.length > 0, decisionNotes);
  push(invitationsById[getInvitationId(number, DECISION_APPROVAL_NAME)],
    decisionApprovalNotes.length > 0, decisionApprovalNotes);

  var cameraReadyRevisionInvitation = invitationsById[getInvitationId(number, CAMERA_READY_REVISION_NAME)];
  if (cameraReadyRevisionInvitation) {
    var cameraReadyComplete = submission.invitations.indexOf(cameraReadyRevisionInvitation.id) > -1;
    push(cameraReadyRevisionInvitation, cameraReadyComplete, cameraReadyComplete ? [1] : []);
  }
  push(invitationsById[getInvitationId(number, CAMERA_READY_VERIFICATION_NAME)],
    cameraReadyVerificationNotes.length > 0, cameraReadyVerificationNotes);
  push(invitationsById[getInvitationId(number, RETRACTION_APPROVAL_NAME)],
    retractionApprovalNotes.length > 0, retractionApprovalNotes);

  return {
    tasks: tasks,
    earlylateTaskDueDate: earlylateTaskDueDate,
    reviewNotes: reviewNotes,
    officialRecommendationNotes: officialRecommendationNotes,
    decisionNotes: decisionNotes,
    ratingReplies: ratingReplies
  };
};

var buildRow = function(submission, context) {
  var number = submission.number;
  var reviewers = context.reviewersByNumber[number] || [];
  var actionEditors = context.aeByNumber[number] || [];
  var invitationsById = context.invitationsById;
  var ratingInvitations = context.ratingsByNumber[number] || [];
  var recommendationCount = context.recommendationCounts[submission.id] || 0;

  var formattedSubmission = {
    id: submission.id,
    forum: submission.forum,
    number: number,
    cdate: submission.cdate,
    mdate: submission.mdate,
    tcdate: submission.tcdate,
    tmdate: submission.tmdate,
    showDates: true,
    content: Object.keys(submission.content).reduce(function(content, key) {
      content[key] = submission.content[key].value;
      return content;
    }, {}),
    referrerUrl: rowReferrerUrl
  };

  var built = buildTasks(submission, invitationsById, ratingInvitations, reviewers, recommendationCount);
  var reviewNotes = built.reviewNotes;

  var recommendationByReviewer = {};
  built.officialRecommendationNotes.forEach(function(recommendation) {
    recommendationByReviewer[recommendation.signatures[0]] = recommendation;
  });

  var anonRoleName = REVIEWERS_NAME.slice(0, -1) + '_';
  var paperReviewerStatus = {};
  reviewers.forEach(function(reviewer) {
    var completedReview = reviewNotes.find(function(review) {
      return review.signatures[0].endsWith('/' + anonRoleName + reviewer.anonId);
    });
    var assignmentAcknowledgement = getReplies(submission, reviewer.id + '/' + ASSIGNMENT_ACKNOWLEDGEMENT_NAME, REVIEWERS_NAME);
    var reviewerRecommendation = null;
    var status = {};

    if (assignmentAcknowledgement && assignmentAcknowledgement.length) {
      status.Acknowledged = 'Yes';
    }
    if (completedReview) {
      reviewerRecommendation = recommendationByReviewer[completedReview.signatures[0]];
      if (reviewerRecommendation) {
        status.Recommendation = reviewerRecommendation.content?.decision_recommendation?.value || 'Yes';
        status.Certifications = reviewerRecommendation.content?.certification_recommendations
          ? reviewerRecommendation.content.certification_recommendations.value.join(', ')
          : '';
      }
      var reviewerRating = built.ratingReplies.find(function(reply) {
        return reply.replyto === completedReview.id;
      });
      if (reviewerRating && reviewerRating.content?.rating) {
        status.Rating = reviewerRating.content.rating.value;
      }
    }

    paperReviewerStatus[reviewer.anonId] = {
      id: reviewer.id,
      name: reviewer.name,
      email: reviewer.email,
      completedReview: !!completedReview,
      completedRecommendation: !!reviewerRecommendation,
      hasRecommendationStarted: !!invitationsById[getInvitationId(number, OFFICIAL_RECOMMENDATION_NAME)],
      forum: submission.id,
      note: completedReview && completedReview.id,
      status: status,
      links: {
        Report: '/forum?id=' + REVIEWER_REPORT_ID + '&noteId=' + REVIEWER_REPORT_ID +
          '&invitationId=' + REVIEWERS_REPORT_ID + '&edit.note.content.reviewer_id=' + reviewer.id +
          '&referrer=' + rowReferrerUrl
      },
      forumUrl: 'https://openreview.net/forum?' + $.param({
        id: submission.id,
        noteId: submission.id,
        invitationId: getInvitationId(number, REVIEW_NAME)
      }),
      anonymousGroupId: reviewer.anonymousGroupId
    };
  });

  var decision = built.decisionNotes.length ? built.decisionNotes[0] : null;
  var metaReview = decision ? {
    id: decision.id,
    forum: submission.id,
    content: {
      recommendation: decision.content?.recommendation?.value,
      certification: (decision.content?.certifications && decision.content.certifications.value) || []
    }
  } : null;

  // Replies readable only by the EICs. Every field this needs is already in
  // SUBMISSION_SELECT, so it costs nothing beyond the page fetch.
  var eicComments = submission.details.replies.filter(function(reply) {
    return reply.readers && reply.readers.length === 1 && reply.readers[0] === EDITORS_IN_CHIEF_ID;
  }).sort(function(a, b) {
    return a.tcdate - b.tcdate;
  });

  var actionEditor = actionEditors.length ? actionEditors[0] : { id: 'No Action Editor' };
  var venueid = submission.content.venueid.value;

  var aeActions = [UNDER_REVIEW_STATUS, SUBMITTED_STATUS, ASSIGNED_AE_STATUS, ASSIGNING_AE_STATUS].indexOf(venueid) > -1 ? [
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
      url: submission.content['previous_' + VENUE_ID + '_submission_url'].value
    });
  }

  return {
    checked: { noteId: submission.id, checked: false },
    submissionNumber: { number: parseInt(number, 10) },
    submission: formattedSubmission,
    reviewProgressData: {
      noteId: submission.id,
      paperNumber: number,
      numSubmittedReviews: reviewNotes.length,
      numSubmittedRecommendations: built.officialRecommendationNotes.length,
      numReviewers: reviewers.length,
      reviewers: paperReviewerStatus,
      expandReviewerList: true,
      sendReminder: true,
      showPreferredEmail: PREFERRED_EMAILS_ID,
      referrer: rowReferrerUrl,
      actions: (venueid === UNDER_REVIEW_STATUS && invitationsById[getInvitationId(number, 'Assignment', REVIEWERS_NAME)]) ? [
        {
          name: 'Edit Assignments',
          url: '/edges/browse?start=staticList,type:head,ids:' + submission.id +
            '&traverse=' + REVIEWERS_ASSIGNMENT_ID +
            '&edit=' + REVIEWERS_ASSIGNMENT_ID + ';' + REVIEWERS_INVITE_ASSIGNMENT_ID + ';' + REVIEWERS_CUSTOM_MAX_PAPERS_ID + ',head:ignore;' + REVIEWERS_AVAILABILITY_ID + ',head:ignore' +
            '&browse=' + REVIEWERS_ARCHIVED_ASSIGNMENT_ID + ';' + REVIEWERS_AFFINITY_SCORE_ID + ';' + REVIEWERS_CONFLICT_ID + ';' + REVIEWERS_PENDING_REVIEWS_ID + ',head:ignore;' +
            '&version=2' +
            '&filter=' + REVIEWERS_PENDING_REVIEWS_ID + ' == 0 AND ' + REVIEWERS_AVAILABILITY_ID + ' == Available AND ' + REVIEWERS_CONFLICT_ID + ' == 0'
        }
      ] : [],
      duedate: (invitationsById[getInvitationId(number, REVIEW_NAME)] || {}).duedate || 0
    },
    actionEditorProgressData: {
      recommendation: metaReview && metaReview.content.recommendation,
      status: { Certification: metaReview ? metaReview.content.certification.join(', ') : '' },
      numMetaReview: metaReview ? 'One' : 'No',
      areachair: !actionEditor.name ? { name: 'No Action Editor' } : { id: actionEditor.id, name: actionEditor.name },
      actionEditor: actionEditor,
      metaReview: metaReview,
      referrer: rowReferrerUrl,
      earlylateTaskDueDate: built.earlylateTaskDueDate,
      metaReviewName: 'Decision',
      committeeName: 'Action Editor',
      actions: aeActions,
      tableWidth: '100%',
      showPreferredEmail: PREFERRED_EMAILS_ID
    },
    tasks: { invitations: built.tasks, forumId: submission.id },
    eicComments: { comments: eicComments },
    status: submission.content.venue?.value
  };
};

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------
var tabState = {};

var renderControls = function(tab) {
  var state = tabState[tab.id];
  var options = SORT_OPTIONS.map(function(option) {
    return '<option value="' + option.value + '"' + (option.value === state.sort ? ' selected' : '') + '>' + option.label + '</option>';
  }).join('');
  return '<form class="form-inline notes-search-form well mb-3" role="search">' +
    '<div class="form-group"><label class="mr-2">Sort:</label> ' +
    '<select class="form-control tab-sort">' + options + '</select></div>' +
    '<div class="form-group" style="margin-left: 1.5rem;"><label class="mr-2">Paper number:</label> ' +
    '<input type="number" min="1" class="form-control tab-number" style="width: 8rem;"' +
    (state.filterNumber ? ' value="' + state.filterNumber + '"' : '') + '> ' +
    '<button type="submit" class="btn btn-default">Filter</button> ' +
    (state.filterNumber ? '<button type="button" class="btn btn-link tab-clear">Clear</button>' : '') +
    '</div></form>';
};

var renderPagination = function(tab, totalCount, pageNumber) {
  var $container = $('#' + tab.id);
  $container.find('.pagination-container').remove();
  if (totalCount <= PAGE_SIZE) {
    return;
  }
  $container.append(view.paginationLinks(totalCount, PAGE_SIZE, pageNumber, null, { showCount: true }));
  $container.find('ul.pagination').css({ marginTop: '2.5rem', marginBottom: '0' });
};

var renderTable = function(tab, rows) {
  Webfield2.ui.renderTable('#' + tab.id + ' .rows-container', rows, {
    headings: ['<input type="checkbox" class="select-all-papers">', '#', 'Paper Summary', 'Review Progress', 'Action Editor Decision', 'Tasks', 'EIC Comments', 'Status'],
    renders: [
      function(data) {
        return '<label><input type="checkbox" class="select-note-reviewers" data-note-id="' + data.noteId + '"></label>';
      },
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      Handlebars.templates.noteSummary,
      Handlebars.templates.noteReviewers,
      Handlebars.templates.noteAreaChairs,
      function(data) {
        return Webfield2.ui.eicTaskList(data.invitations, data.forumId, { referrer: referrerUrl, showEditLink: true });
      },
      function(data) {
        if (!data.comments.length) {
          return '<span class="text-muted">&mdash;</span>';
        }
        return '<ul class="list-unstyled">' + data.comments.map(function(comment) {
          return '<li class="mb-3">' +
            '<p class="text-muted mb-1">' + view.forumDate(comment.tcdate) + ': </p>' +
            '<p class="mb-1" style="white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">' +
            '<strong><a href="https://openreview.net/forum?id=' + comment.forum + '&noteId=' + comment.id +
            '" target="_blank" rel="nofollow">' + (comment.content?.title?.value ?? 'Comment') + '</a></strong></p>' +
            '<p style="word-break: break-word;">' + (comment.content?.comment?.value ?? '') + '</p>' +
            '</li>';
        }).join('\n') + '</ul>';
      },
      function(data) {
        return '<h4>' + (data || '') + '</h4>';
      }
    ],
    extraClasses: 'console-table paper-table',
    reminderOptions: {
      container: 'a.send-reminder-link',
      defaultSubject: SHORT_PHRASE + ' Reminder',
      defaultBody: 'Hi {{fullname}},\n\nThis is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n' +
        'Click on the link below to go to the submission page:\n\n{{forumUrl}}\n\n' +
        'Thank you,\n' + SHORT_PHRASE + ' Editor-in-Chief',
      replyTo: EDITORS_IN_CHIEF_EMAIL,
      messageInvitationId: VENUE_ID + '/-/Edit',
      messageSignature: VENUE_ID,
      // No bulk Message dropdown on this console yet.
      //
      // Webfield2.ui.renderTable only inserts that dropdown inside the bar it
      // builds for `sortOptions`, and sorting here is server-side over the whole
      // tab, so passing sortOptions would put a second, client-side sort control
      // next to this one that silently reorders only the loaded page. Rendering
      // the dropdown from renderControls instead means this console owns its
      // toolbar; that is the intended fix, deferred for now.
      //
      // The rest of reminderOptions is live: the per-reviewer "send reminder"
      // links in the Review Progress column are bound independently of
      // sortOptions and work today.
      //
      // When the dropdown is added, it acts on the current page: selection can
      // only reach loaded rows, which is narrower than the same menu item in the
      // unpaginated console, where it covers the whole tab.
    },
    postRenderTable: function() {
      // Sums to 100. The number column has to hold four digits, and Status
      // holds a full venue string such as "Under review for TMLR", so neither
      // can take the leftovers.
      var widths = ['2%', '5%', '18%', '17%', '16%', '16%', '16%', '10%'];
      widths.forEach(function(width, index) {
        $('#' + tab.id + ' .console-table th').eq(index).css('width', width);
      });
    },
    preferredEmailsInvitationId: PREFERRED_EMAILS_ID
  });
};

// Loads and renders one page. Every request issued here is scoped to the page.
var showPage = function(tab, pageNumber) {
  var state = tabState[tab.id];
  state.page = pageNumber;
  state.requestId = (state.requestId || 0) + 1;
  var requestId = state.requestId;

  var $container = $('#' + tab.id);
  $container.html(renderControls(tab) + '<div class="rows-container"><p class="empty-message">Loading...</p></div>');

  return loadSubmissionPage(tab, pageNumber, state).then(function(page) {
    var numbers = page.submissions.map(function(submission) { return submission.number; });
    return $.when(
      loadPageInvitations(numbers),
      loadPageGroups(numbers),
      loadRecommendationCounts()
    ).then(function(pageInvitations, groups, recommendationCounts) {
      // A slower earlier page must not overwrite a later one the user has
      // already moved to.
      if (state.requestId !== requestId) {
        return;
      }
      var rows = page.submissions.map(function(submission) {
        return buildRow(submission, {
          invitationsById: pageInvitations.invitationsById,
          ratingsByNumber: pageInvitations.ratingsByNumber,
          reviewersByNumber: groups.reviewersByNumber,
          aeByNumber: groups.aeByNumber,
          recommendationCounts: recommendationCounts
        });
      });
      if (!rows.length) {
        $container.find('.rows-container').html('<p class="empty-message">No papers to display at this time.</p>');
      } else {
        renderTable(tab, rows);
      }
      renderPagination(tab, page.count, pageNumber);
    });
  }).fail(function(error) {
    var message = (error && error.message) ? error.message : 'unknown error';
    $container.find('.rows-container').html('<p class="empty-message">Error loading papers: ' + message + '</p>');
  });
};

var bindTabHandlers = function(tab) {
  var $container = $('#' + tab.id);

  $container.on('click', 'ul.pagination > li > a', function() {
    var $target = $(this).parent();
    if ($target.hasClass('disabled') || $target.hasClass('active')) {
      return false;
    }
    var pageNumber = parseInt($target.data('pageNumber'), 10);
    if (!isNaN(pageNumber)) {
      showPage(tab, pageNumber);
    }
    return false;
  });

  $container.on('change', '.tab-sort', function() {
    tabState[tab.id].sort = $(this).val();
    showPage(tab, 1);
  });

  $container.on('submit', 'form', function() {
    var value = parseInt($container.find('.tab-number').val(), 10);
    tabState[tab.id].filterNumber = isNaN(value) ? null : value;
    showPage(tab, 1);
    return false;
  });

  $container.on('click', '.tab-clear', function() {
    tabState[tab.id].filterNumber = null;
    showPage(tab, 1);
    return false;
  });
};

// Pending Editors-in-Chief tasks.
//
// The original console accumulated these while looping over every submission,
// which is why it needed the whole venue in memory. The same list is available
// directly: an approval invitation that is still live is a task that is still
// open, and details=repliedNotes says whether it has been answered. Non-expired
// is the default, and expire_paper_invitations() expires a paper's invitations
// when it reaches a terminal state, so finished papers drop out on the server.
//
// Three requests, plus one to resolve titles for whatever came back pending.
// The result is bounded by the number of open tasks, not by the venue.
var EIC_APPROVAL_NAMES = [DESK_REJECTION_APPROVAL_NAME, DECISION_APPROVAL_NAME, RETRACTION_APPROVAL_NAME];

// The number of open tasks is bounded by the backlog rather than by the venue,
// but a backlog can still be large. Render the most urgent ones and say how
// many were held back, rather than building an arbitrarily long list.
var PENDING_TASKS_SHOWN = 25;

var loadPendingEicTasks = function() {
  var requests = EIC_APPROVAL_NAMES.map(function(name) {
    return Webfield2.api.get('/invitations', {
      invitation: VENUE_ID + '/-/' + name,
      details: 'repliedNotes',
      select: 'id,cdate,duedate,details',
      domain: VENUE_ID
    }).then(function(result) {
      return (result.invitations || []).filter(function(invitation) {
        var replied = invitation.details && invitation.details.repliedNotes;
        return !replied || !replied.length;
      });
    }, function() {
      return [];
    });
  });

  return $.when.apply($, requests).then(function() {
    var pending = [];
    Array.prototype.slice.call(arguments).forEach(function(invitations) {
      pending = pending.concat(invitations || []);
    });
    if (!pending.length) {
      return { total: 0, tasks: [] };
    }
    pending.sort(function(a, b) { return (a.duedate || 0) - (b.duedate || 0); });
    var totalPending = pending.length;
    pending = pending.slice(0, PENDING_TASKS_SHOWN);

    // Resolve the paper titles in one request. The invitation id carries the
    // paper number, so no per-task lookup is needed.
    var numbers = pending.map(function(invitation) {
      return Webfield2.utils.getNumberfromInvitation
        ? Webfield2.utils.getNumberfromInvitation(invitation.id, SUBMISSION_GROUP_NAME)
        : invitation.id.split('/' + SUBMISSION_GROUP_NAME)[1].split('/')[0];
    });

    return Webfield2.api.get('/notes', {
      invitation: SUBMISSION_ID,
      number: numbers.join(','),
      domain: VENUE_ID,
      select: 'id,number,content.title'
    }).then(function(result) {
      var notesByNumber = {};
      (result.notes || []).forEach(function(note) {
        notesByNumber[note.number] = note;
      });
      return {
        total: totalPending,
        tasks: pending.map(function(invitation, index) {
          var note = notesByNumber[numbers[index]];
          return {
            invitation: invitation,
            forumId: note ? note.id : null,
            title: note ? (note.content.title ? note.content.title.value : note.number) : ('Paper ' + numbers[index])
          };
        })
      };
    }, function() {
      return {
        total: totalPending,
        tasks: pending.map(function(invitation, index) {
          return { invitation: invitation, forumId: null, title: 'Paper ' + numbers[index] };
        })
      };
    });
  });
};

var renderPendingEicTasks = function(pending) {
  var tasks = (pending && pending.tasks) || [];
  if (!tasks.length) {
    return '<p class="empty-message mb-3">No tasks to complete.</p>';
  }
  var dateFormatOptions = {
    hour: 'numeric', minute: 'numeric', day: '2-digit', month: 'short', year: 'numeric', timeZoneName: 'long'
  };
  var now = Date.now();
  var html = '<ul class="list-unstyled submissions-list task-list eic-task-list mt-0 mb-0">';
  tasks.forEach(function(task) {
    var duedate = task.invitation.duedate ? new Date(task.invitation.duedate) : null;
    var dueStatus = duedate && duedate.getTime() < now ? 'expired' : '';
    var link = task.forumId
      ? '/forum?id=' + task.forumId + '&invitationId=' + task.invitation.id + '&referrer=' + referrerUrl
      : '/invitation/edit?id=' + task.invitation.id;
    html += '<li class="note">' +
      '<p class="mb-1"><strong><a href="' + link + '" target="_blank">' +
      task.title + ': ' + view.prettyInvitationId(task.invitation.id) + '</a></strong></p>' +
      (duedate
        ? '<p class="mb-1"><span class="duedate ' + dueStatus + '" style="margin-left: 0;">Due: ' +
          duedate.toLocaleDateString('en-GB', dateFormatOptions) + '</span></p>'
        : '') +
      '</li>';
  });
  html += '</ul>';
  if (pending.total > tasks.length) {
    html += '<p class="hint mt-2">Showing the ' + tasks.length + ' most urgent of ' +
      pending.total + ' open tasks.</p>';
  }
  return html;
};

// The overview asks only for counts: limit 1 with an offset makes the API
// return count without the console having to hold the documents.
var renderOverview = function() {
  var buckets = [
    { label: 'Submitted', venueids: [SUBMITTED_STATUS, ASSIGNING_AE_STATUS, ASSIGNED_AE_STATUS] },
    { label: 'Under Review', venueids: [UNDER_REVIEW_STATUS] },
    { label: 'Decision Pending', venueids: [DECISION_PENDING_STATUS] },
    { label: 'Accepted', venueids: [VENUE_ID] },
    { label: 'Rejected', venueids: [REJECTED_STATUS, DESK_REJECTED_STATUS] },
    { label: 'Withdrawn', venueids: [WITHDRAWN_STATUS] },
    { label: 'Retracted', venueids: [RETRACTED_STATUS] }
  ];

  var requests = buckets.map(function(bucket) {
    return Webfield2.api.get('/notes', {
      invitation: SUBMISSION_ID,
      domain: VENUE_ID,
      'content.venueid': bucket.venueids.join(','),
      select: 'id',
      limit: 1,
      offset: 0
    }).then(function(result) {
      return result.count || 0;
    }, function() {
      return null;
    });
  });

  requests.push(Webfield2.api.getGroup(REVIEWERS_ID, {}).then(function(group) {
    return group && group.members ? group.members.length : 0;
  }, function() { return null; }));
  requests.push(Webfield2.api.getGroup(ACTION_EDITOR_ID, {}).then(function(group) {
    return group && group.members ? group.members.length : 0;
  }, function() { return null; }));
  requests.push(loadPendingEicTasks().then(null, function() { return { total: 0, tasks: [] }; }));

  return $.when.apply($, requests).then(function() {
    var values = Array.prototype.slice.call(arguments);
    var stat = function(title, value, hint) {
      return '<div class="col-md-3 col-xs-6 mb-3"><h4>' + title + '</h4><h3>' +
        (value === null || value === undefined ? '&mdash;' : value) + '</h3>' +
        (hint ? '<p class="hint">' + hint + '</p>' : '') + '</div>';
    };
    var html = '<div class="container"><div class="row text-center" style="margin-top: .5rem;">';
    html += stat('Reviewers', values[buckets.length],
      '<a href="/group/edit?id=' + REVIEWERS_ID + '">Reviewers Group</a>');
    html += stat('Action Editors', values[buckets.length + 1],
      '<a href="/group/edit?id=' + ACTION_EDITOR_ID + '">Action Editors Group</a>');
    html += '</div><hr class="spacer"><div class="row text-center">';
    buckets.forEach(function(bucket, index) {
      html += stat(bucket.label, values[index]);
    });
    html += '</div>';
    html += '<hr class="spacer"><div class="row"><div class="col-md-6">' +
      '<h4>Pending Editors-in-Chief Tasks:</h4>' +
      renderPendingEicTasks(values[buckets.length + 2]) +
      '</div></div>';
    html += '</div>';
    $('#overview').html(html);
  });
};

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------
var main = function() {
  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Overview'].concat(SUBMISSION_TABS.map(function(tab) { return tab.label; })),
    referrer: args && args.referrer,
    fullWidth: true
  });

  if (!user || user.isGuest) {
    Webfield2.ui.errorMessage('You must be logged in to access this page.');
    return;
  }

  SUBMISSION_TABS.forEach(function(tab) {
    tabState[tab.id] = { page: 1, sort: SORT_OPTIONS[0].value, filterNumber: null, loaded: false };
    bindTabHandlers(tab);
  });

  // A tab fetches on first activation and not before, so opening the console
  // costs the overview counts rather than the whole venue.
  $('#group-container').on('shown.bs.tab', 'ul.nav-tabs li a', function() {
    var tabId = ($(this).attr('href') || '').replace('#', '');
    var tab = SUBMISSION_TABS.find(function(candidate) { return candidate.id === tabId; });
    if (tab && !tabState[tab.id].loaded) {
      tabState[tab.id].loaded = true;
      showPage(tab, 1);
    }
  });

  renderOverview().always(function() {
    Webfield2.ui.done();
  });
};

main();
