
// Constants
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var BLIND_SUBMISSION_ID = '';
var HEADER = {};
var REVIEWER_NAME = '';
var OFFICIAL_REVIEW_NAME = '';
var LEGACY_INVITATION_ID = false;
var REVIEW_LOAD = 0;

var WILDCARD_INVITATION = CONFERENCE_ID + '/.*';
var ANONREVIEWER_WILDCARD = CONFERENCE_ID + '/Paper.*/AnonReviewer.*';
var CUSTOM_LOAD_INVITATION = CONFERENCE_ID + '/-/Reduced_Load';

var main = function() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  OpenBanner.venueHomepageLink(CONFERENCE_ID);

  displayHeader();

  var userIds = _.union(user.profile.usernames, user.profile.emails);

  getReviewerNoteNumbers()
    .then(function(noteNumbers) {
      return $.when(
        getBlindedNotes(noteNumbers),
        getReviewRatings(noteNumbers),
        getOfficialReviews(noteNumbers),
        getReviewerGroups(noteNumbers),
        getNoteInvitations(),
        getEdgeInvitations(),
        getTagInvitations(),
        getCustomLoad(userIds)
      );
    })
    .then(function(
      blindedNotes,
      reviewRatings,
      officialReviews,
      noteToReviewerIds,
      invitations,
      edgeInvitations,
      tagInvitations,
      customLoad
    ) {
      if (customLoad > 0) {
        $('#header .description').append(
          '<p class="dark">You have agreed to review up to <strong>' + customLoad + ' papers</strong>.</p>'
        );
      }

      displayStatusTable(blindedNotes, reviewRatings, officialReviews, noteToReviewerIds);

      displayTasks(invitations, edgeInvitations, tagInvitations);

      Webfield.ui.done();
    })
    .fail(function(error) {
      displayError();
    });
};

// Helper functions
var getNumberFromGroup = function(groupId, name) {
  var paper = groupId.split('/').find(function(token) {
    return token.indexOf(name) === 0;
  });

  if (paper) {
    return parseInt(paper.substring(name.length), 10);
  }
  return null;
};

var getInvitationId = function(name, number) {
  return LEGACY_INVITATION_ID
    ? CONFERENCE_ID + '/-/Paper' + number + '/' + name
    : CONFERENCE_ID + '/Paper' + number + '/-/' + name;
};

var buildNoteMap = function(noteNumbers) {
  var noteMap = Object.create(null);
  for (var i = 0; i < noteNumbers.length; i++) {
    noteMap[noteNumbers[i]] = Object.create(null);
  }
  return noteMap;
};

// AJAX functions
var getReviewerNoteNumbers = function() {
  return Webfield.get('/groups', {
    member: user.id,
    regex: ANONREVIEWER_WILDCARD
  }).then(function(result) {
    if (!result.groups) {
      return [];
    }
    return _.without(result.groups.map(function(group) {
      return getNumberFromGroup(group.id, 'Paper');
    }), null);
  });
};

var getBlindedNotes = function(noteNumbers) {
  if (!noteNumbers || !noteNumbers.length) {
    return $.Deferred().resolve([]);
  }

  return Webfield.get('/notes', {
    invitation: BLIND_SUBMISSION_ID, number: noteNumbers.join(',')
  }).then(function(result) {
    return result.notes || [];
  });
};

var getReviewRatings = function(noteNumbers) {
  if (!noteNumbers || !noteNumbers.length) {
    return $.Deferred().resolve([]);
  }

  var noteMap = buildNoteMap(noteNumbers);

  return Webfield.getAll('/notes', {
    invitation: getInvitationId('Review_Rating', '.*')
  }).then(function(notes) {
    notes.forEach(function(note) {
      var num = getNumberFromGroup(note.invitation, 'Paper');
      if (num in noteMap) {
        noteMap[num][note.forum] = note;
      }
    });
    return noteMap;
  });
};

var getReviewerGroups = function(noteNumbers) {
  if (!noteNumbers || !noteNumbers.length) {
    return $.Deferred().resolve([]);
  }

  var noteMap = buildNoteMap(noteNumbers);
  var userIds = [];

  return Webfield.get('/groups', { id: ANONREVIEWER_WILDCARD })
    .then(function(result) {
      if (!result.groups) {
        return noteMap;
      }
      result.groups.forEach(function(g) {
        if (!g.members.length) {
          return;
        }
        var num = getNumberFromGroup(g.id, 'Paper');
        var index = getNumberFromGroup(g.id, 'AnonReviewer');
        if (num && index && (num in noteMap)) {
          noteMap[num][index] = g.members[0];
          userIds.push(g.members[0]);
        }
      });

      return getUserProfiles(_.uniq(userIds));
    })
    .then(function(profiles) {
      for (var paperNum in noteMap) {
        var reviewerMap = noteMap[paperNum];
        for (var reviewerNum in reviewerMap) {
          var id = reviewerMap[reviewerNum];
          reviewerMap[reviewerNum] = profiles[id] || { id: id, name: '', email: id };
        }
      }
      return noteMap;
    });
};

var getUserProfiles = function(userIds) {
  if (!userIds || !userIds.length) {
    return $.Deferred().resolve([]);
  }

  return Webfield.post('/user/profiles', { ids: userIds }).then(function(result) {
    var profileMap = {};
    if (!result || !result.profiles) {
      return profileMap;
    }

    result.profiles.forEach(function(profile) {
      var name = _.find(profile.content.names, ['preferred', true]) || _.first(profile.content.names);
      profile.name = _.isEmpty(name) ? view.prettyId(profile.id) : name.first + ' ' + name.last;
      profile.email = profile.content.preferredEmail;
      profileMap[profile.id] = profile;
    })

    return profileMap;
  });
};

var getOfficialReviews = function(noteNumbers) {
  if (!noteNumbers || !noteNumbers.length) {
    return $.Deferred().resolve([]);
  }

  return Webfield.get('/notes', {
    invitation: getInvitationId(OFFICIAL_REVIEW_NAME, '.*'), tauthor: true
  }).then(function(result) {
    return result.notes || [];
  });
};

var getNoteInvitations = function() {
  return Webfield.get('/invitations', {
    regex: WILDCARD_INVITATION,
    invitee: true,
    duedate: true,
    replyto: true,
    type: 'notes',
    details: 'replytoNote,repliedNotes'
  }).then(function(result) {
    return result.invitations || [];
  });
};

var getEdgeInvitations = function() {
  return Webfield.get('/invitations', {
    regex: WILDCARD_INVITATION,
    invitee: true,
    duedate: true,
    type: 'edges',
    details: 'repliedEdges'
  }).then(function(result) {
    return result.invitations || [];
  });
};

var getTagInvitations = function() {
  return Webfield.get('/invitations', {
    regex: WILDCARD_INVITATION,
    invitee: true,
    duedate: true,
    type: 'tags',
    details: 'repliedTags'
  }).then(function(result) {
    return result.invitations || [];
  });
};

var getCustomLoad = function(userIds) {
  if (REVIEW_LOAD <= 0) {
    return $.Deferred().resolve(0);
  }

  return Webfield.get('/notes', { invitation: CUSTOM_LOAD_INVITATION })
    .then(function(result) {
      if (!result.notes || !result.notes.length) {
        return REVIEW_LOAD;
      }
      if (result.notes.length === 1) {
        return result.notes[0].content.reviewer_load;
      } else {
        // If there is more than one there might be a Program Chair
        var loads = result.notes.filter(function(note) {
          return userIds.indexOf(note.content.user) > -1;
        });
        return loads.length ? loads[0].content.reviewer_load : REVIEW_LOAD;
      }
    });
};

// Render functions
var displayHeader = function() {
  Webfield.ui.venueHeader(HEADER);

  var loadingMessage = '<p class="empty-message">Loading...</p>';
  var tabs = [
    {
      heading: 'Assigned Papers',
      id: 'assigned-papers',
      content: loadingMessage,
      active: true
    },
    {
      heading: 'Reviewer Tasks',
      id: 'reviewer-tasks',
      content: loadingMessage,
    }
  ];
  Webfield.ui.tabPanel(tabs, {
    container: '#notes'
  });
};

var displayStatusTable = function(notes, completedRatings, officialReviews, reviewerIds) {
  var $container = $('#assigned-papers');

  if (Object.keys(reviewerIds).length === 0) {
    $container.empty().append('<p class="empty-message">You have no assigned papers. Please check again after the paper assignment process. ');
  }

  var rowData = notes.map(function(note) {
    var officialReview = _.find(officialReviews, ['invitation', getInvitationId(OFFICIAL_REVIEW_NAME, note.number)]);
    return buildTableRow(
      note, reviewerIds[note.number], completedRatings[note.number], officialReview
    );
  });

  var tableHTML = Handlebars.templates['components/table']({
    headings: ['#', 'Paper Summary', 'Your Ratings'],
    rows: rowData,
    extraClasses: 'console-table'
  });

  $container.empty().append(tableHTML);
};

var buildTableRow = function(note, reviewerIds, completedRatings, officialReview) {
  var referrerUrl = encodeURIComponent('[Reviewer Console](/group?id=' + CONFERENCE_ID + '/' + REVIEWER_NAME + '#assigned-papers)');
  var number = '<strong class="note-number">' + note.number + '</strong>';

  // Build Note Summary Cell
  var cell1 = note;
  cell1.content.authors = null;  // Don't display 'Blinded Authors'
  cell1.referrer = referrerUrl;
  // note.content.authorDomains = domains;
  var summaryHtml = Handlebars.templates.noteSummary(cell1);

  // Build Status Cell
  var invitationUrlParams = {
    id: note.forum,
    noteId: note.id,
    invitationId: getInvitationId(OFFICIAL_REVIEW_NAME, note.number),
    referrer: referrerUrl
  };
  var reviewStatus = {
    invitationUrl: '/forum?' + $.param(invitationUrlParams),
    invitationName: 'Official Review'
  };
  if (officialReview) {
    reviewStatus.paperRating = officialReview.content.rating;
    reviewStatus.review = officialReview.content.review;
    reviewStatus.editUrl = '/forum?id=' + note.forum + '&noteId=' + officialReview.id + '&referrer=' + referrerUrl;
  }
  var statusHtml = Handlebars.templates.noteReviewStatus(reviewStatus);

  return [number, summaryHtml, statusHtml];
};

var displayTasks = function(invitations, edgeInvitations, tagInvitations) {
  //  My Tasks tab
  var tasksOptions = {
    container: '#reviewer-tasks',
    emptyMessage: 'No outstanding tasks for this conference',
    referrer: encodeURIComponent('[Reviewer Console](/group?id=' + CONFERENCE_ID + '/' + REVIEWER_NAME + '#reviewer-tasks)')
  }
  $(tasksOptions.container).empty();

  // Filter out non-reviewer tasks
  var filterFunc = function(inv) {
    return _.some(inv.invitees, function(invitee) { return invitee.indexOf(REVIEWER_NAME) > -1; });
  };
  var reviewerInvitations = _.filter(invitations, filterFunc);
  var reviewerEdgeInvitations = _.filter(edgeInvitations, filterFunc);
  var reviewerTagInvitations = _.filter(tagInvitations, filterFunc);

  Webfield.ui.newTaskList(reviewerInvitations, reviewerEdgeInvitations.concat(reviewerTagInvitations), tasksOptions)
  $('.tabs-container a[href="#reviewer-tasks"]').parent().show();
};

var displayError = function(message) {
  message = message || 'Reviewer console could not be loaded. Please try again later.';
  $('#notes').empty().append('<div class="alert alert-danger"><strong>Error:</strong> ' + message + '</div>');
};


// Kick the whole thing off
main();

// Register event handlers
$('#group-container').on('click', 'a.note-contents-toggle', function(e) {
  var hiddenText = 'Show paper details';
  var visibleText = 'Hide paper details';
  var updated = $(this).text() === hiddenText ? visibleText : hiddenText;
  $(this).text(updated);
});

$('#group-container').on('click', 'a.send-reminder-link', function(e) {
  var userId = $(this).data('userId');
  var forumUrl = $(this).data('forumUrl');
  var postData = {
    groups: [userId],
    subject: SHORT_PHRASE + ' Reminder',
    message: 'This is a reminder to please submit your review for ' + SHORT_PHRASE + '. ' +
      'Click on the link below to go to the review page:\n\n' + location.origin + forumUrl + '\n\nThank you.'
  };

  return Webfield.post('/messages', postData).then(function() {
    // Save the timestamp in the local storage
    localStorage.setItem(forumUrl + '|' + userId, Date.now());
    promptMessage('A reminder email has been sent to ' + view.prettyId(userId));
    renderTable();
  });
});
