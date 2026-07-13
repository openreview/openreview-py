var main = function() {
  Webfield2.ui.setup('#invitation-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    referrer: (args && args.referrer) || JMLR_VENUE_REFERRER,
    fullWidth: true
  });
  JMLRPermissionHelpers.renderVenueHomepageStrip({
    container: '#invitation-container',
    venueId: VENUE_ID,
    $: $
  });
  
  if (!user || user.isGuest) {
    Webfield2.ui.errorMessage('You must be logged in to access this page.');
    return;
  }

  Webfield2.api.getGroup(EDITORS_IN_CHIEF_ID)
    .then(function(editorsInChiefGroup) {
      var helpers = typeof JMLRPermissionHelpers !== 'undefined' ? JMLRPermissionHelpers : null;
      var eicGroupCache = {};
      eicGroupCache[EDITORS_IN_CHIEF_ID] = editorsInChiefGroup;
      var actorContext = helpers && helpers.loadActorContext
        ? helpers.loadActorContext(user || {}).model.actor_context
        : null;
      var paperContext = helpers && helpers.loadPaperContext
        ? helpers.loadPaperContext({ groups: eicGroupCache }).model.paper_context
        : { groups: eicGroupCache };
      var venueContext = helpers && helpers.loadVenueContext
        ? helpers.loadVenueContext({
          venue_id: VENUE_ID,
          role_groups: {
            eic: EDITORS_IN_CHIEF_ID
          }
        }).model.venue_context
        : { venue_id: VENUE_ID, role_groups: { eic: EDITORS_IN_CHIEF_ID } };
      var roleAccess = helpers && helpers.getRoleContextAccessModel && actorContext
        ? helpers.getRoleContextAccessModel(actorContext, paperContext, {
          entry_point: 'assign_action_editor',
          requested_role_context: getAssignActionEditorRoleContext(),
          required_role_context: 'eic',
          venue_context: venueContext
        })
        : { ok: assignmentPageHasEicRoleContext() && currentUserIsEic(editorsInChiefGroup), reasons: [] };
      if (!roleAccess.ok) {
        ASSIGN_AE_ROLE_CONTEXT_ALLOWED = false;
        Webfield2.ui.errorMessage('Open this page from the editor-in-chief role context to assign an action editor.');
        return $.Deferred().reject().promise();
      }
      ASSIGN_AE_ROLE_CONTEXT_ALLOWED = true;
      if (!currentUserIsEic(editorsInChiefGroup)) {
        Webfield2.ui.errorMessage('You must be an editor-in-chief to access this page.');
        return $.Deferred().reject().promise();
      }
      return loadData()
        .then(formatData)
        .then(renderAssignActionEditorInvitation)
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

var getAssignmentOpenReviewConflictByTailMap = function(headId) {
  var conflictSources = actionEditorAssignmentConflictSources();
  return $.when(
    getEdgesByTailMap(conflictSources.openreviewConflictInvitation, headId),
    getEdgesByTailMap(conflictSources.reviewerConflictInvitation, headId)
  ).then(function(actionEditorConflictByTail, reviewerConflictByTail) {
    actionEditorConflictByTail = actionEditorConflictByTail || {};
    reviewerConflictByTail = reviewerConflictByTail || {};
    return _.uniq(Object.keys(actionEditorConflictByTail).concat(Object.keys(reviewerConflictByTail))).reduce(function(byTail, tail) {
      byTail[tail] = actionEditorConflictByTail[tail] || reviewerConflictByTail[tail];
      return byTail;
    }, {});
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

var loadData = function() {
  var availabilitySources = actionEditorAssignmentAvailabilitySources();
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
    Webfield2.api.getGroup(EDITORS_IN_CHIEF_ID),
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
    getEdgesByTailMap(availabilitySources.actionEditorAvailabilityInvitation, availabilitySources.actionEditorGroup),
    getAssignmentOpenReviewConflictByTailMap(ASSIGN_AE_PAPER_ID),
    Webfield2.api.getAll('/edges', {
      invitation: actionEditorAssignmentInvitationId(),
      head: ASSIGN_AE_PAPER_ID
    }),
    Webfield2.api.get('/notes', { id: ASSIGN_AE_PAPER_ID, domain: VENUE_ID }).then(function(result) {
      return result && result.notes && result.notes[0] || null;
    }, function() {
      return null;
    })
  );
};

var updateEarlyLateTaskDuedate = function(earlylateTaskDueDate, task) {
  if ((earlylateTaskDueDate == 0 || earlylateTaskDueDate > task.duedate) && !task.complete) {
    earlylateTaskDueDate = task.duedate;
  }
  return earlylateTaskDueDate;
}
