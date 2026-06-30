var main = function() {
  var tabs = [
    'Pending Tasks',
    'Active Papers',
    'Decision Made',
    'Camera Ready',
    'All Submissions',
    'Role Statistics',
    'Action Editor Status',
    'Reviewer Status',
    'Assign Roles',
    'Bulk Invite'
  ];
  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: tabs,
    referrer: args && args.referrer,
    fullWidth: true
  });
  JMLRPermissionHelpers.renderVenueHomepageStrip({ container: '#group-container', venueId: VENUE_ID, $: $ });
  
  if (!user || user.isGuest) {
    Webfield2.ui.errorMessage('You must be logged in to access this page.');
    return;
  }  

  Webfield2.api.getGroup(EDITORS_IN_CHIEF_ID)
    .then(function(editorsInChiefGroup) {
      if (!currentUserIsEic(editorsInChiefGroup)) {
        Webfield2.ui.errorMessage('You must be an editor-in-chief to access this page.');
        return $.Deferred().reject().promise();
      }
      return loadData()
        .then(formatData)
        .then(renderData)
        .then(Webfield2.ui.done);
    })
    .fail(function(error) {
      if (error) Webfield2.ui.errorMessage(error);
    });
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

var getEdgesByTailMap = function(invitationId, headId) {
  return Webfield2.api.getAll('/edges', { invitation: invitationId, head: headId, domain: VENUE_ID })
    .then(function(edges) {
      return (edges || []).reduce(function(byTail, edge) {
        byTail[edge.tail] = edge;
        return byTail;
      }, {});
    }, function() {
      return {};
    });
};

var getGroupSafe = function(groupId, options) {
  return Webfield2.api.getGroup(groupId, options).then(function(group) {
    if (!group) {
      return {
        id: groupId,
        members: [],
        exists: false
      };
    }
    group.exists = true;
    return group;
  }, function() {
    return {
      id: groupId,
      members: [],
      exists: false
    };
  });
};

var groupActiveEdgesByHead = function(edges) {
  return (edges || []).reduce(function(byHead, edge) {
    if (!edge || edge.ddate || !edge.head) return byHead;
    byHead[edge.head] = byHead[edge.head] || [];
    byHead[edge.head].push(edge);
    return byHead;
  }, {});
};

var getPaperActionEditorAssignmentEdges = function(submissions) {
  var submittedStatusValues = [
    SUBMITTED_STATUS,
    ASSIGNING_AE_STATUS,
    ASSIGNED_AE_STATUS,
    UNDER_REVIEW_STATUS,
    DECISION_PENDING_STATUS
  ];
  var assignmentEdgeRequests = (submissions || []).filter(function(submission) {
    return submission
      && submission.number
      && submission.id
      && submission.content
      && submission.content.venueid
      && submittedStatusValues.includes(submission.content.venueid.value);
  }).map(function(submission) {
    return Webfield2.api.getAll('/edges', {
      invitation: VENUE_ID + '/Paper' + submission.number + '/Action_Editors/-/Assignment',
      head: submission.id,
      domain: VENUE_ID
    }).then(function(edges) {
      return edges || [];
    }, function() {
      return [];
    });
  });
  if (!assignmentEdgeRequests.length) {
    var emptyResult = $.Deferred();
    emptyResult.resolve([]);
    return emptyResult.promise();
  }
  return $.when.apply($, assignmentEdgeRequests).then(function() {
    return Array.prototype.concat.apply([], Array.prototype.slice.call(arguments));
  });
};

var loadData = function() {
  return $.when(
    Webfield2.api.getGroupsByNumber(VENUE_ID, ACTION_EDITOR_NAME),
    Webfield2.api.getGroupsByNumber(VENUE_ID, REVIEWERS_NAME, { withProfiles: true}),
    Webfield2.api.getAllSubmissions(SUBMISSION_ID, { domain: VENUE_ID, limit: CONSOLE_FETCH_LIMIT }),
    Webfield2.api.getGroup(VENUE_ID + '/' + ACTION_EDITOR_NAME, { withProfiles: true}),
    Webfield2.api.getGroup(VENUE_ID + '/' + ACTION_EDITOR_NAME + '/Archived', { withProfiles: true}),
    OSS_ACTION_EDITORS_ENABLED ? getGroupSafe(OSS_ACTION_EDITORS_ID, { withProfiles: true }) : $.Deferred().resolve({ members: [] }).promise(),
    Webfield2.api.getGroup(VENUE_ID + '/' + REVIEWERS_NAME, { withProfiles: true}),
    Webfield2.api.getGroup(VENUE_ID + '/' + REVIEWERS_NAME + '/Archived', { withProfiles: true}),
    Webfield2.api.getGroup(VENUE_ID + '/' + REVIEWERS_NAME + '/Volunteers', { withProfiles: true}),
    getGroupSafe(EXPERT_REVIEWERS_ID, { withProfiles: true }),
    getGroupSafe(PRODUCTION_EDITORS_ID, { withProfiles: true }),
    getGroupSafe(AUTHORS_ID),
    Webfield2.api.getGroup(EDITORS_IN_CHIEF_ID, { withProfiles: true }),
    Webfield2.api.get('/notes', { id: JOURNAL_REQUEST_ID }).then(function(result) {
      return result.notes && result.notes[0];
    }),
    Webfield2.api.get('/invitations', {
      prefix: VENUE_ID + '/' + SUBMISSION_GROUP_NAME,
      type: 'all',
      select: 'id,cdate,duedate,expdate',
      domain: VENUE_ID,
      stream: true
    }).then(function(result) {
      return _.keyBy(result.invitations, 'id');
    }),
    Webfield2.api.get('/notes', {
      invitation: VENUE_ID + '/-/Setup_Assignments',
      domain: VENUE_ID,
      limit: 1000,
      sort: 'tcdate:desc'
    }).then(function(result) {
      return result.notes || [];
    }, function() {
      return [];
    }),
    Webfield2.api.get('/invitations', { prefix: VENUE_ID + '/-/.*', select: 'id', expired: true, sort: 'cdate:asc', domain: VENUE_ID, stream: true }).then(function(result) { return result.invitations; }),
    Webfield2.api.get('/invitations', { prefix: REVIEWERS_ID + '/-/.*', select: 'id', expired: true, sort: 'cdate:asc', domain: VENUE_ID, stream: true }).then(function(result) { return result.invitations; }),
    Webfield2.api.get('/invitations', { prefix: ACTION_EDITOR_ID + '/-/.*', select: 'id', expired: true, sort: 'cdate:asc', domain: VENUE_ID, stream: true }).then(function(result) { return result.invitations; }),
    Webfield2.api.get('/edges', { invitation: ACTION_EDITORS_RECOMMENDATION_ID, groupBy: 'head', select: 'count', domain: VENUE_ID})
    .then(function(response) {
      var groupedEdges = response.groupedEdges;
      var recommendationCount = {};
      groupedEdges.forEach(function(group){
        recommendationCount[group.id.head] = group.count;
      })
      return recommendationCount;
    }),
    Webfield2.api.get('/settings/institutiondomains').then(function(result) {
      institutionDomains = result;
    }),
    getEdgesByTailMap(REVIEWERS_AVAILABILITY_ID, REVIEWERS_ID),
    getEdgesByTailMap(ACTION_EDITORS_AVAILABILITY_ID, ACTION_EDITOR_ID)
  ).then(function() {
    var args = Array.prototype.slice.call(arguments);
    var submissions = args[2] || [];
    return getPaperActionEditorAssignmentEdges(submissions).then(function(actionEditorAssignmentEdges) {
      var loadedData = $.Deferred();
      args.push(actionEditorAssignmentEdges || []);
      loadedData.resolve.apply(loadedData, args);
      return loadedData.promise();
    });
  });
};

var updateEarlyLateTaskDuedate = function(earlylateTaskDueDate, task) {
  if ((earlylateTaskDueDate == 0 || earlylateTaskDueDate > task.duedate) && !task.complete) {
    earlylateTaskDueDate = task.duedate;
  }
  return earlylateTaskDueDate;
}
