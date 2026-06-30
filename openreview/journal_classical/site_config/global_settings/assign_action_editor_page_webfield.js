var ASSIGN_AE_WEBFIELD_SOURCE_GROUP_ID = 'JMLR/Editors_In_Chief';
var ASSIGN_AE_WEBFIELD_CONTENT_KEY = 'assign_action_editor_webfield_script';
var ASSIGN_AE_SETUP_INVITATION_ID = 'JMLR/-/Setup_Assignments';
var ASSIGN_AE_SETUP_READINESS_STATUS = 'Assignment pages created';

(function() {
  var pageArgs = typeof args !== 'undefined' && args ? args : {};
  var pagePaperId = pageArgs.assignAePaper || pageArgs.paperId || '';
  var pageAssignmentInvitationId = pageArgs.assignmentInvitation || '';
  var pageAssignmentBrowserContract = pageArgs.assignmentBrowserContract || {};
  var currentUser = typeof user !== 'undefined' && user ? user : {};

  var asList = function(value) {
    if (!value) return [];
    return Array.isArray(value) ? value : [value];
  };

  var userIdentifiers = function() {
    var profile = currentUser.profile || {};
    var ids = [];
    [currentUser.id, profile.id, profile.preferredId, profile.preferredEmail].forEach(function(value) {
      if (value && ids.indexOf(value) < 0) ids.push(value);
    });
    asList(profile.emails).concat(asList(profile.usernames)).forEach(function(value) {
      if (value && ids.indexOf(value) < 0) ids.push(value);
    });
    return ids;
  };

  var currentUserIsEic = function(eicGroup) {
    var members = asList(eicGroup && eicGroup.members);
    var ids = userIdentifiers();
    return ids.some(function(id) { return members.indexOf(id) >= 0; });
  };

  var setStatus = function(message) {
    var $container = $('#group-container');
    if (!$container.length) $container = $('body');
    $container.html('<div class="container"><p class="text-muted"></p></div>');
    $container.find('p').first().text(message);
  };

  var showError = function(message) {
    if (typeof Webfield2 !== 'undefined' && Webfield2.ui && Webfield2.ui.errorMessage) {
      Webfield2.ui.errorMessage(message);
    } else {
      var $container = $('#group-container');
      if (!$container.length) $container = $('body');
      $container.html('<div class="alert alert-danger" role="alert"></div>');
      $container.children().first().text(String(message));
    }
  };

  var runScript = function(source) {
    if (!source) {
      showError('The Action Editor assignment page webfield is not installed.');
      return;
    }
    if (!pagePaperId) {
      showError('The Action Editor assignment page needs a selected paper.');
      return;
    }
    source = String(source).replace(/#invitation-container/g, '#group-container');
    (new Function(
      'args',
      'user',
      'ASSIGN_AE_PAPER_ID',
      'ASSIGN_AE_ASSIGNMENT_INVITATION_ID',
      'ASSIGN_AE_ASSIGNMENT_BROWSER_CONTRACT',
      source
    ))(pageArgs, currentUser, pagePaperId, pageAssignmentInvitationId, pageAssignmentBrowserContract);
  };

  var readScript = function(group) {
    return group && group.content && group.content[ASSIGN_AE_WEBFIELD_CONTENT_KEY] && group.content[ASSIGN_AE_WEBFIELD_CONTENT_KEY].value;
  };

  var currentPageUrl = function() {
    var pageLocation = (typeof globalThis !== 'undefined' && globalThis.location) || {};
    return pageLocation.href || '';
  };

  var redirectWithAssignmentInvitation = function(assignmentInvitationId) {
    var href = currentPageUrl();
    if (!href) return;
    var url = new URL(href);
    url.searchParams.set('assignmentInvitation', assignmentInvitationId);
    globalThis.location.replace(url.toString());
  };

  var getSelectedPaper = function() {
    if (!pagePaperId) {
      return $.Deferred().reject('The Action Editor assignment page needs a selected paper.').promise();
    }
    return Webfield2.api.get('/notes', { id: pagePaperId, domain: 'JMLR' }).then(function(result) {
      var notes = result && result.notes || [];
      if (!notes.length) {
        return $.Deferred().reject('The selected paper is not readable or does not exist.').promise();
      }
      return notes[0];
    });
  };

  var assignmentInvitationIdForPaper = function(note) {
    return 'JMLR/Paper' + note.number + '/Action_Editors/-/Assignment';
  };

  var contentValue = function(content, key) {
    var field = content && content[key];
    return field && Object.prototype.hasOwnProperty.call(field, 'value') ? field.value : field;
  };

  var setupReadinessMatches = function(setupNote, paperNote) {
    var content = setupNote && setupNote.content || {};
    return String(contentValue(content, 'note_id') || '') === String(paperNote.id || '') &&
      Number(contentValue(content, 'paper_number')) === Number(paperNote.number) &&
      contentValue(content, 'setup_readiness_status') === ASSIGN_AE_SETUP_READINESS_STATUS;
  };

  var assignmentSetupReady = function(note) {
    return Webfield2.api.get('/notes', {
      invitation: ASSIGN_AE_SETUP_INVITATION_ID,
      domain: 'JMLR',
      limit: 50,
      sort: 'tcdate:desc'
    }).then(function(result) {
      var notes = result && result.notes || [];
      return notes.some(function(setupNote) {
        return setupReadinessMatches(setupNote, note);
      });
    }, function() {
      return false;
    });
  };

  var assignmentInvitationExists = function(assignmentInvitationId) {
    return Webfield2.api.get('/invitations', { id: assignmentInvitationId, select: 'id', domain: 'JMLR' }).then(function(result) {
      var invitations = result && result.invitations || [];
      return invitations.length > 0;
    }, function() {
      return false;
    });
  };

  var wait = function(milliseconds) {
    var deferred = $.Deferred();
    setTimeout(function() {
      deferred.resolve();
    }, milliseconds);
    return deferred.promise();
  };

  var waitForAssignmentSetup = function(note, assignmentInvitationId, attempt) {
    var currentAttempt = attempt || 0;
    return $.when(
      assignmentInvitationExists(assignmentInvitationId),
      assignmentSetupReady(note)
    ).then(function(invitationExists, isReady) {
      if (invitationExists && isReady) {
        pageAssignmentInvitationId = assignmentInvitationId;
        return assignmentInvitationId;
      }
      if (currentAttempt >= 45) {
        return $.Deferred().reject('Timed out waiting for assignment pages for Paper ' + note.number + '. Refresh the EIC console and try Assign Action Editor again.').promise();
      }
      return wait(2000).then(function() {
        return waitForAssignmentSetup(note, assignmentInvitationId, currentAttempt + 1);
      });
    });
  };

  var setupPaperAssignment = function(note, assignmentInvitationId, options) {
    options = options || {};
    setStatus((options.refreshOnly ? 'Refreshing assignment checks for Paper ' : 'Creating the assignment pages for Paper ') + note.number + '...');
    return Webfield2.api.post('/notes/edits', {
      invitation: ASSIGN_AE_SETUP_INVITATION_ID,
      signatures: ['JMLR/Editors_In_Chief'],
      note: {
        content: {
          note_id: { value: note.id },
          paper_number: { value: note.number }
        }
      }
    }).then(function() {
      return waitForAssignmentSetup(note, assignmentInvitationId, 0);
    }).then(function() {
      if (!options.refreshOnly) redirectWithAssignmentInvitation(assignmentInvitationId);
      return assignmentInvitationId;
    });
  };

  var ensureAssignmentInvitation = function(note) {
    var assignmentInvitationId = pageAssignmentInvitationId || assignmentInvitationIdForPaper(note);
    return assignmentInvitationExists(assignmentInvitationId).then(function(invitationExists) {
      return assignmentSetupReady(note).then(function(isReady) {
        if (invitationExists && isReady) {
          pageAssignmentInvitationId = assignmentInvitationId;
          return setupPaperAssignment(note, assignmentInvitationId, { refreshOnly: true });
        }
        return setupPaperAssignment(note, assignmentInvitationId);
      });
    }, function() {
      return setupPaperAssignment(note, assignmentInvitationId);
    }).then(function(readyAssignmentInvitationId) {
      if (readyAssignmentInvitationId) {
        pageAssignmentInvitationId = assignmentInvitationId;
      }
      return readyAssignmentInvitationId;
    });
  };

  if (typeof Webfield2 === 'undefined' || !Webfield2.api || !Webfield2.api.get) {
    showError('OpenReview Webfield2 API is unavailable.');
    return;
  }

  Webfield2.api.get('/groups', {
    id: ASSIGN_AE_WEBFIELD_SOURCE_GROUP_ID,
    limit: 1,
    select: 'id,members,content'
  }).then(function(result) {
    var group = result && result.groups && result.groups[0];
    if (!group) {
      showError('The Action Editor assignment page source group is not readable.');
      return;
    }
    if (!currentUserIsEic(group)) {
      showError('Only JMLR Editors in Chief can use this assignment page.');
      return;
    }
    return getSelectedPaper().then(function(note) {
      return ensureAssignmentInvitation(note);
    }).then(function(assignmentInvitationId) {
      if (!assignmentInvitationId) return;
      runScript(readScript(group));
    });
  }).fail(function(error) {
    showError(error && (error.message || (error.responseJSON && error.responseJSON.message)) || error || 'Could not load the Action Editor assignment page.');
  });
}());
