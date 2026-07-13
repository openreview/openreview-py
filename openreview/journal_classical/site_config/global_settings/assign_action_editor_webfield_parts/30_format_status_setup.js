var formatData = function(
  aeByNumber,
  reviewersByNumber,
  submissions,
  actionEditors,
  archivedActionEditors,
  ossActionEditors,
  reviewers,
  archivedReviewers,
  volunteerReviewers,
  expertReviewers,
  productionEditors,
  authorsGroup,
  editorsInChiefGroup,
  journalRequestNote,
  invitationsById,
  superInvitationIds,
  reviewerInvitationIds,
  aeInvitationIds,
  aeRecommendations,
  institutionDomainsResult,
  reviewerAvailabilityByTail,
  actionEditorAvailabilityByTail,
  actionEditorConflictByTail,
  actionEditorAssignmentEdges,
  selectedPaperNote
) {
  var referrerUrl = encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + '#paper-status)');
  actionEditors = actionEditors || { members: [] };
  actionEditors.members = (actionEditors.members || []).filter(Boolean);
  archivedActionEditors = archivedActionEditors || { members: [] };
  archivedActionEditors.members = (archivedActionEditors.members || []).filter(Boolean);
  ossActionEditors = ossActionEditors || { members: [] };
  ossActionEditors.members = (ossActionEditors.members || []).filter(Boolean);
  reviewers = reviewers || { members: [] };
  reviewers.members = (reviewers.members || []).filter(Boolean);
  archivedReviewers = archivedReviewers || { members: [] };
  archivedReviewers.members = (archivedReviewers.members || []).filter(Boolean);
  volunteerReviewers = volunteerReviewers || { members: [] };
  volunteerReviewers.members = (volunteerReviewers.members || []).filter(Boolean);
  expertReviewers = expertReviewers || { members: [] };
  expertReviewers.members = (expertReviewers.members || []).filter(Boolean);
  productionEditors = productionEditors || { members: [] };
  productionEditors.members = (productionEditors.members || []).filter(Boolean);
  editorsInChiefGroup = editorsInChiefGroup || { content: {} };

  var getGroupContentValue = function(group, key) {
    return group && group.content && group.content[key] && group.content[key].value;
  };
  var getNoteContentValue = function(note, key) {
    return note && note.content && note.content[key] && note.content[key].value;
  };
  var journalSettings = getNoteContentValue(journalRequestNote, 'settings') || {};
  var ossActionEditorsMaxPapers = Number(journalSettings.oss_action_editors_max_papers || 20);
  var aeAvailabilitySources = actionEditorAssignmentAvailabilitySources();
  actionEditorConflictByTail = actionEditorConflictByTail || {};
  var actionEditorAssignmentEdgesByHead = groupActiveEdgesByHead(actionEditorAssignmentEdges || []);
  if (selectedPaperNote && !submissions.some(function(submission) { return submission.id === selectedPaperNote.id; })) {
    selectedPaperNote.details = selectedPaperNote.details || {};
    selectedPaperNote.details.replies = selectedPaperNote.details.replies || [];
    submissions = submissions.concat([selectedPaperNote]);
  }

  var reviewerStatusById = {};
  var getAvailabilityData = function(invitationId, headId, profileId, edge, enabled) {
    return {
      invitationId: invitationId,
      headId: headId,
      tailId: profileId,
      edgeId: edge && edge.id,
      label: edge && edge.label || 'Available',
      weight: edge && edge.weight,
      enabled: enabled
    };
  };
  var hasInstitutionEmail = function(member) {
    return (member.allEmails || []).some(function(email) {
      return institutionDomains.includes(email.split('@')[1]);
    });
  };
  var getInstitutionLabel = function(member) {
    var content = member && member.content || {};
    var history = content.history || [];
    for (var i = history.length - 1; i >= 0; i -= 1) {
      var institution = history[i] && history[i].institution;
      if (institution && (institution.name || institution.domain)) {
        return institution.name || institution.domain;
      }
    }
    var institutionEmail = (member.allEmails || []).find(function(email) {
      var domain = String(email || '').split('@')[1];
      return domain && institutionDomains.includes(domain);
    });
    return institutionEmail ? institutionEmail.split('@')[1] : '';
  };
  var isIndefinitelyUnavailable = function(edge) {
    return edge && edge.label === 'Unavailable' && !edge.weight;
  };

  var getReviewerStatus = function(reviewer, index, isReviewer, isArchived, isVolunteer, isExpertReviewer) {
    var availabilityEdge = reviewerAvailabilityByTail[reviewer.id];
    var isActive = isReviewer && !isArchived && !isIndefinitelyUnavailable(availabilityEdge);
    return {
      index: { number: index + 1 },
	      summary: {
	        id: reviewer.id,
	        name: reviewer.name,
        email: reviewer.email,
        status: {
          Profile: reviewer.id.startsWith('~') ? 'Yes' : 'No',
          Active: isActive ? 'Active' : 'Not active',
          'Top Reviewer': isExpertReviewer ? 'Yes' : 'No'
	        },
	        hasInstitutionEmail: hasInstitutionEmail(reviewer)
	      },
	      availabilityData: getAvailabilityData(
	        REVIEWERS_AVAILABILITY_ID,
	        REVIEWERS_ID,
	        reviewer.id,
	        availabilityEdge,
	        isReviewer && !isArchived
	      ),
	      reviewerProgressData: {
	        numCompletedReviews: 0,
	        numPapers: 0,
        papers: [],
        referrer: referrerUrl
      },
      ratingData: {
        ratings:[],
        ratingsMap: Object.keys(REVIEWER_RATING_MAP).reduce((o, key) => Object.assign(o, {[key]: 0}), {}),
        timelinessMap: (JMLRPermissionHelpers && JMLRPermissionHelpers.REVIEWER_TIMELINESS_ORDER || ['On time', 'Past due', 'Review not expected']).reduce((o, key) => Object.assign(o, {[key]: 0}), {}),
        averageRating: 0,
        ratingCount: 0,
        ratingTotal: 0
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
  var reviewerIds = new Set();
  var archivedReviewerIds = new Set();
  var expertReviewerIds = new Set((expertReviewers.members || []).map(function(reviewer) {
    return reviewer.id;
  }));
  reviewers.members.forEach(function(reviewer, index) {
    reviewerStatusById[reviewer.id] = getReviewerStatus(reviewer, index, true, false, false, expertReviewerIds.has(reviewer.id));
    reviewerIds.add(reviewer.id);
  });

  (archivedReviewers?.members || []).forEach(function(reviewer, index) {
    reviewerStatusById[reviewer.id] = getReviewerStatus(reviewer, index, false, true, false, expertReviewerIds.has(reviewer.id));
    archivedReviewerIds.add(reviewer.id);
  });

  (volunteerReviewers?.members || []).forEach(function(reviewer, index) {
    reviewerStatusById[reviewer.id] = getReviewerStatus(reviewer, index, reviewerIds.has(reviewer.id), archivedReviewerIds.has(reviewer.id), true, expertReviewerIds.has(reviewer.id));
  });  

  var actionEditorStatusById = {};
  var ossActionEditorIds = new Set((ossActionEditors.members || []).map(function(actionEditor) {
    return actionEditor.id;
  }));
  actionEditors.members.forEach(function(actionEditor, index) {
    var availabilityEdge = actionEditorAvailabilityByTail[actionEditor.id];
    var isActive = !isIndefinitelyUnavailable(availabilityEdge);
    actionEditorStatusById[actionEditor.id] = {
      index: { number: index + 1 },
      summary: {
        id: actionEditor.id,
        name: actionEditor.name,
        email: actionEditor.email,
        allEmails: actionEditor.allEmails || [],
        profileContent: actionEditor.content || {},
        institution: getInstitutionLabel(actionEditor),
        status: {
          Profile: actionEditor.id.startsWith('~') ? 'Yes' : 'No',
          Active: isActive ? 'Active' : 'Not active',
          'OSS AE': isOssActionEditorProfile(actionEditor.id, ossActionEditorIds) ? 'Yes' : 'No'
	        },
	        hasInstitutionEmail: hasInstitutionEmail(actionEditor)
	      },
	      availabilityData: getAvailabilityData(
	        aeAvailabilitySources.actionEditorAvailabilityInvitation,
	        aeAvailabilitySources.actionEditorGroup,
	        actionEditor.id,
	        availabilityEdge,
	        true
	      ),
	      conflictData: actionEditorConflictByTail[actionEditor.id],
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
	      },
        decisionTimingData: {
          completedWithinSixMonths: 0,
          completedWithinNineMonths: 0,
          completedOverTwelveMonths: 0,
          pendingWithinSixMonths: 0
        }
	    };
  });

  archivedActionEditors.members.forEach(function(actionEditor, index) {
    var availabilityEdge = actionEditorAvailabilityByTail[actionEditor.id];
    actionEditorStatusById[actionEditor.id] = {
      index: { number: index + 1 },
      summary: {
        id: actionEditor.id,
        name: actionEditor.name,
        email: actionEditor.email,
        allEmails: actionEditor.allEmails || [],
        profileContent: actionEditor.content || {},
        institution: getInstitutionLabel(actionEditor),
        status: {
          Profile: actionEditor.id.startsWith('~') ? 'Yes' : 'No',
          Active: 'Not active',
          'OSS AE': isOssActionEditorProfile(actionEditor.id, ossActionEditorIds) ? 'Yes' : 'No'
	        },
	        hasInstitutionEmail: hasInstitutionEmail(actionEditor)
	      },
	      availabilityData: getAvailabilityData(
	        aeAvailabilitySources.actionEditorAvailabilityInvitation,
	        aeAvailabilitySources.actionEditorGroup,
	        actionEditor.id,
	        availabilityEdge,
	        false
	      ),
	      conflictData: actionEditorConflictByTail[actionEditor.id],
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
	      },
        decisionTimingData: {
          completedWithinSixMonths: 0,
          completedWithinNineMonths: 0,
          completedOverTwelveMonths: 0,
          pendingWithinSixMonths: 0
        }
	    };
	  });  

  var paperStatusRows = [];
  var authorSubmissionsCount = {};
  var incompleteEicTasks = [];
  var overdueTasks = [];
  submissions.forEach(function(submission) {
    var number = submission.number;
    var roleContext = resolveConsolePaperRoleContext(submission, 'eic', EDITORS_IN_CHIEF_ID);
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
      previousSubmissionUrl: getPreviousSubmissionUrl(submission),
      paperUrl: appendRoleContext('/forum?id=' + encodeURIComponent(submission.id) + '&referrer=' + referrerUrl, roleContext),
      roleContext: roleContext,
      referrerUrl: referrerUrl
    };
    var paperActionEditors = aeByNumber[number] || [];
    var actionEditor = { id: 'No Action Editor' };
    if (paperActionEditors.length && actionEditorStatusById[paperActionEditors[0].id]) {
      actionEditor = actionEditorStatusById[paperActionEditors[0].id].summary;
    }
    var activeActionEditorAssignmentEdge = (actionEditorAssignmentEdgesByHead[submission.id] || []).find(function(edge) {
      return edge && !edge.ddate && edge.tail;
    }) || null;
    if (activeActionEditorAssignmentEdge) {
      actionEditor = actionEditorStatusById[activeActionEditorAssignmentEdge.tail]
        ? actionEditorStatusById[activeActionEditorAssignmentEdge.tail].summary
        : {
          id: activeActionEditorAssignmentEdge.tail,
          name: activeActionEditorAssignmentEdge.tail
        };
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
