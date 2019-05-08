
// Constants
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var BLIND_SUBMISSION_ID = '';
var HEADER = {};
var AREA_CHAIR_NAME = '';
var OFFICIAL_REVIEW_NAME = '';
var OFFICIAL_META_REVIEW_NAME = '';
var LEGACY_INVITATION_ID = false;

var WILDCARD_INVITATION = CONFERENCE_ID + '.*';
var ANONREVIEWER_WILDCARD = CONFERENCE_ID + '/Paper.*/AnonReviewer.*';
var AREACHAIR_WILDCARD = CONFERENCE_ID + '/Paper.*/Area_Chair.*';

// Main function is the entry point to the webfield code
var main = function() {
  OpenBanner.venueHomepageLink(CONFERENCE_ID);

  renderHeader();

  Webfield.get('/groups', {
    member: user.id, regex: AREACHAIR_WILDCARD
  })
  .then(loadData)
  .then(formatData)
  .then(renderTableAndTasks)
  .fail(function() {
    Webfield.ui.errorMessage();
  });
};


// Util functions
var getNumberfromGroup = function(groupId, name) {

  var tokens = groupId.split('/');
  paper = _.find(tokens, function(token) { return token.startsWith(name); });
  if (paper) {
    return parseInt(paper.replace(name, ''));
  } else {
    return null;
  }
};

var getPaperNumbersfromGroups = function(groups) {
  return _.filter(_.map(groups, function(group) {
    return getNumberfromGroup(group.id, 'Paper');
  }), _.isInteger);
};

var buildNoteMap = function(noteNumbers) {
  var noteMap = Object.create(null);
  for (var i = 0; i < noteNumbers.length; i++) {
    noteMap[noteNumbers[i]] = Object.create(null);
  }
  return noteMap;
};

var getInvitationId = function(name, number) {
  if (LEGACY_INVITATION_ID) {
    return CONFERENCE_ID + '/-/Paper' + number + '/' + name;
  }
  return CONFERENCE_ID + '/Paper' + number + '/-/' + name;
}

// Ajax functions
var loadData = function(result) {
  var noteNumbers = getPaperNumbersfromGroups(result.groups);
  var blindedNotesP;
  var metaReviewsP;

  if (noteNumbers.length) {
    var noteNumbersStr = noteNumbers.join(',');

    blindedNotesP = Webfield.getAll('/notes', {
      invitation: BLIND_SUBMISSION_ID, number: noteNumbersStr, noDetails: true
    });

    metaReviewsP = Webfield.getAll('/notes', {
      invitation: getInvitationId(OFFICIAL_META_REVIEW_NAME, '.*'), noDetails: true
    });
  } else {
    blindedNotesP = $.Deferred().resolve([]);
    metaReviewsP = $.Deferred().resolve([]);
  }

  var invitationsP = Webfield.getAll('/invitations', {
    regex: WILDCARD_INVITATION, invitee: true,
    duedate: true, replyto: true, details: 'replytoNote,repliedNotes'
  });

  var tagInvitationsP = Webfield.getAll('/invitations', {
    regex: WILDCARD_INVITATION,
    invitee: true,
    duedate: true,
    tags: true,
    details:'repliedTags'
  });

  return $.when(
    blindedNotesP,
    getOfficialReviews(noteNumbers),
    metaReviewsP,
    getReviewerGroups(noteNumbers),
    invitationsP,
    tagInvitationsP
  );
};

var getOfficialReviews = function(noteNumbers) {
  if (!noteNumbers.length) {
    return $.Deferred().resolve({});
  }

  var noteMap = buildNoteMap(noteNumbers);

  return Webfield.getAll('/notes', {
    invitation: getInvitationId(OFFICIAL_REVIEW_NAME, '.*'), noDetails: true
  })
  .then(function(notes) {
    var ratingExp = /^(\d+): .*/;

    _.forEach(notes, function(n) {
      var num = getNumberfromGroup(n.signatures[0], 'Paper');
      var index = getNumberfromGroup(n.signatures[0], 'AnonReviewer');
      if (num) {
        if (num in noteMap) {
          // Need to parse rating and confidence strings into ints
          ratingMatch = n.content.rating.match(ratingExp);
          n.rating = ratingMatch ? parseInt(ratingMatch[1], 10) : null;
          confidenceMatch = n.content.confidence.match(ratingExp);
          n.confidence = confidenceMatch ? parseInt(confidenceMatch[1], 10) : null;

          noteMap[num][index] = n;
        }
      }
    });

    return noteMap;
  });
};

var getReviewerGroups = function(noteNumbers) {
  if (!noteNumbers.length) {
    return $.Deferred().resolve({});
  };

  var noteMap = buildNoteMap(noteNumbers);

  return Webfield.getAll('/groups', { id: ANONREVIEWER_WILDCARD })
  .then(function(groups) {
    _.forEach(groups, function(g) {
      var num = getNumberfromGroup(g.id, 'Paper');
      var index = getNumberfromGroup(g.id, 'AnonReviewer');
      if (num) {
        if ((num in noteMap) && g.members.length) {
          noteMap[num][index] = g.members[0];
        }
      }
    });

    return noteMap;
  });
};

var formatData = function(blindedNotes, officialReviews, metaReviews, noteToReviewerIds, invitations, tagInvitations) {
  var uniqueIds = _.uniq(_.reduce(noteToReviewerIds, function(result, idsObj, noteNum) {
    return result.concat(_.values(idsObj));
  }, []));

  return getUserProfiles(uniqueIds)
  .then(function(profiles) {
    return {
      profiles: profiles,
      blindedNotes: blindedNotes,
      officialReviews: officialReviews,
      metaReviews: metaReviews,
      noteToReviewerIds: noteToReviewerIds,
      invitations: invitations,
      tagInvitations: tagInvitations
    };
  });
};

var getUserProfiles = function(userIds) {
  var profileMap = {};

  return Webfield.post('/user/profiles', { ids: userIds })
  .then(function(result) {
    _.forEach(result.profiles, function(profile) {
      var name = _.find(profile.content.names, ['preferred', true]) || _.first(profile.content.names);
      profile.name = _.isEmpty(name) ? view.prettyId(profile.id) : name.first + ' ' + name.last;
      profile.email = profile.content.preferredEmail || profile.content.emails[0];
      profileMap[profile.id] = profile;
    });

    return profileMap;
  });
};


// Render functions
var renderHeader = function() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);
  Webfield.ui.header(HEADER.title, HEADER.instructions);

  var loadingMessage = '<p class="empty-message">Loading...</p>';
  Webfield.ui.tabPanel([
    {
      heading: 'Assigned Papers',
      id: 'assigned-papers',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll',
      active: true
    },
    {
      heading: 'Area Chair Schedule',
      id: 'areachair-schedule',
      content: HEADER.schedule
    },
    {
      heading: 'Area Chair Tasks',
      id: 'areachair-tasks',
      content: loadingMessage
    }
  ]);
};

var renderStatusTable = function(profiles, notes, completedReviews, metaReviews, reviewerIds, container) {
  var rows = _.map(notes, function(note) {
    var revIds = reviewerIds[note.number] || Object.create(null);
    for (var revNumber in revIds) {
      var uId = revIds[revNumber];
      revIds[revNumber] = _.get(profiles, uId, { id: uId, name: '', email: uId });
    }

    var metaReview = _.find(metaReviews, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, note.number)]);
    var noteCompletedReviews = completedReviews[note.number] || Object.create(null);

    return buildTableRow(note, revIds, noteCompletedReviews, metaReview);
  });

  // Sort form handler
  var order = 'desc';
  var sortOptions = {
    Paper_Number: function(row) { return row[1].number; },
    Paper_Title: function(row) { return _.toLower(_.trim(row[2].content.title)); },
    Number_of_Reviews_Submitted: function(row) { return row[3].numSubmittedReviews; },
    Number_of_Reviews_Missing: function(row) { return row[3].numReviewers - row[3].numSubmittedReviews; },
    Average_Rating: function(row) { return row[4].averageRating === 'N/A' ? 0 : row[4].averageRating; },
    Max_Rating: function(row) { return row[4].maxRating === 'N/A' ? 0 : row[4].maxRating; },
    Min_Rating: function(row) { return row[4].minRating === 'N/A' ? 0 : row[4].minRating; },
    Average_Confidence: function(row) { return row[5].averageConfidence === 'N/A' ? 0 : row[5].averageConfidence; },
    Max_Confidence: function(row) { return row[5].maxConfidence === 'N/A' ? 0 : row[5].maxConfidence; },
    Min_Confidence: function(row) { return row[5].minConfidence === 'N/A' ? 0 : row[5].minConfidence; },
    Meta_Review_Rating: function(row) { return row[6].recommendation ? _.toInteger(row[6].recommendation.split(':')[0]) : 0; }
  };
  var sortResults = function(newOption, switchOrder) {
    if (switchOrder) {
      order = order === 'asc' ? 'desc' : 'asc';
    }
    renderTableRows(_.orderBy(rows, sortOptions[newOption], order), container);
  }

  // Message modal handler
  var sendReviewerReminderEmailsStep1 = function(e) {
    var subject = $('#message-reviewers-modal input[name="subject"]').val().trim();
    var message = $('#message-reviewers-modal textarea[name="message"]').val().trim();
    var group   = $('#message-reviewers-modal select[name="group"]').val();
    var filter  = $('#message-reviewers-modal select[name="filter"]').val();

    var count = 0;
    var selectedRows = rows;
    var reviewerMessages = [];
    var reviewerCounts = Object.create(null);
    if (group === 'selected') {
      selectedIds = _.map(
        $('.ac-console-table input.select-note-reviewers:checked'),
        function(checkbox) { return $(checkbox).data('noteId'); }
      );
      selectedRows = rows.filter(function(row) {
        return _.includes(selectedIds, row[2].forum);
      });
    }

    selectedRows.forEach(function(row) {
      var users = _.values(row[3].reviewers);
      if (filter === 'submitted') {
        users = users.filter(function(u) {
          return u.completedReview;
        });
      } else if (filter === 'unsubmitted') {
        users = users.filter(function(u) {
          return !u.completedReview;
        });
      }

      if (users.length) {
        var forumUrl = 'https://openreview.net/forum?' + $.param({
          id: row[2].forum,
          noteId: row[2].id,
          invitationId: getInvitationId(OFFICIAL_REVIEW_NAME, row[2].number)
        });
        reviewerMessages.push({
          groups: _.map(users, 'id'),
          forumUrl: forumUrl,
          subject: subject,
          message: message,
        });

        users.forEach(function(u) {
          if (u.id in reviewerCounts) {
            reviewerCounts[u.id].count++;
          } else {
            reviewerCounts[u.id] = {
              name: u.name,
              email: u.email,
              count: 1
            };
          }
        });

        count += users.length;
      }
    });
    localStorage.setItem('reviewerMessages', JSON.stringify(reviewerMessages));
    localStorage.setItem('messageCount', count);

    // Show step 2
    var namesHtml = _.flatMap(reviewerCounts, function(obj) {
      var text = obj.name + ' <span>&lt;' + obj.email + '&gt;</span>';
      if (obj.count > 1) {
        text += ' (&times;' + obj.count + ')';
      }
      return text;
    }).join(', ');
    $('#message-reviewers-modal .reviewer-list').html(namesHtml);
    $('#message-reviewers-modal .num-reviewers').text(count);
    $('#message-reviewers-modal .step-1').hide();
    $('#message-reviewers-modal .step-2').show();

    return false;
  };

  var sendReviewerReminderEmailsStep2 = function(e) {
    var reviewerMessages = localStorage.getItem('reviewerMessages');
    var messageCount = localStorage.getItem('messageCount');
    if (!reviewerMessages || !messageCount) {
      $('#message-reviewers-modal').modal('hide');
      promptError('Could not send reminder emails at this time. Please refresh the page and try again.');
    }
    JSON.parse(reviewerMessages).forEach(postReviewerEmails);

    localStorage.removeItem('reviewerMessages');
    localStorage.removeItem('messageCount');

    $('#message-reviewers-modal').modal('hide');
    promptMessage('Successfully sent ' + messageCount + ' reminder emails');
  };

  var sortOptionHtml = Object.keys(sortOptions).map(function(option) {
    return '<option value="' + option + '">' + option.replace(/_/g, ' ') + '</option>';
  }).join('\n');

  var sortBarHtml = '<form class="form-inline search-form clearfix" role="search">' +
    '<strong>Sort By:</strong> ' +
    '<select id="form-sort" class="form-control">' + sortOptionHtml + '</select>' +
    '<button id="form-order" class="btn btn-icon"><span class="glyphicon glyphicon-sort"></span></button>' +
    '<div class="pull-right">' +
      '<button id="message-reviewers-btn" class="btn btn-icon"><span class="glyphicon glyphicon-envelope"></span> &nbsp;Message Reviewers</button>' +
    '</div>' +
    '</form>';
  if (rows.length) {
    $(container).empty().append(sortBarHtml);
  }

  // Need to add event handlers for these controls inside this function so they have access to row
  // data
  $('#form-sort').on('change', function(e) {
    sortResults($(e.target).val(), false);
  });
  $('#form-order').on('click', function(e) {
    sortResults($(this).prev().val(), true);
    return false;
  });

  $('#message-reviewers-btn').on('click', function(e) {
    $('#message-reviewers-modal').remove();

    var modalHtml = Handlebars.templates.messageReviewersModal({
      defaultSubject: SHORT_PHRASE + ' Reminder',
      defaultBody: 'This is a reminder to please submit your review for ' + SHORT_PHRASE + '. ' +
        'Click on the link below to go to the review page:\n\n[[SUBMIT_REVIEW_LINK]]' +
        '\n\nThank you,\n' + SHORT_PHRASE + ' Area Chair',
    });
    $('body').append(modalHtml);

    $('#message-reviewers-modal .btn-primary.step-1').on('click', sendReviewerReminderEmailsStep1);
    $('#message-reviewers-modal .btn-primary.step-2').on('click', sendReviewerReminderEmailsStep2);
    $('#message-reviewers-modal form').on('submit', sendReviewerReminderEmailsStep1);

    $('#message-reviewers-modal').modal();

    if ($('.ac-console-table input.select-note-reviewers:checked').length) {
      $('#message-reviewers-modal select[name="group"]').val('selected');
    }
    return false;
  });

  if (rows.length) {
    renderTableRows(rows, container);
  } else {
    $(container).empty().append('<p class="empty-message">No assigned papers. ' +
      'Check back later or contact info@openreview.net if you believe this to be an error.</p>');
  }
};

var renderTableRows = function(rows, container) {
  var templateFuncs = [
    function(data) {
      var checked = data.selected ? 'checked="checked"' : '';
      return '<label><input type="checkbox" class="select-note-reviewers" data-note-id="' +
        data.noteId + '" ' + checked + '></label>';
    },
    function(data) {
      return '<strong class="note-number">' + data.number + '</strong>';
    },
    Handlebars.templates.noteSummary,
    Handlebars.templates.noteReviewers,
    function(data) {
      return '<h4>Avg: ' + data.averageRating + '</h4><span>Min: ' + data.minRating + '</span>' +
        '<br><span>Max: ' + data.maxRating + '</span>';
    },
    function(data) {
      return '<h4>Avg: ' + data.averageConfidence + '</h4><span>Min: ' + data.minConfidence + '</span>' +
        '<br><span>Max: ' + data.maxConfidence + '</span>';
    },
    Handlebars.templates.noteMetaReviewStatus
  ];

  var rowsHtml = rows.map(function(row) {
    return row.map(function(cell, i) {
      return templateFuncs[i](cell);
    });
  });

  var tableHtml = Handlebars.templates['components/table']({
    headings: [
      '<span class="glyphicon glyphicon-envelope"></span>', '#', 'Paper Summary',
      'Review Progress', 'Rating', 'Confidence', 'Status'
    ],
    rows: rowsHtml,
    extraClasses: 'ac-console-table'
  });

  $('.table-container', container).remove();
  $(container).append(tableHtml);
}

var renderTasks = function(invitations, tagInvitations) {
  //  My Tasks tab
  var tasksOptions = {
    container: '#areachair-tasks',
    emptyMessage: 'No outstanding tasks for this conference'
  }
  $(tasksOptions.container).empty();

  // Filter out non-areachair tasks
  var filterFunc = function(inv) {
    return _.some(inv.invitees, function(invitee) { return invitee.indexOf(AREA_CHAIR_NAME) !== -1; });
  };
  var areachairInvitations = _.filter(invitations, filterFunc);
  var areachairTagInvitations = _.filter(tagInvitations, filterFunc);

  Webfield.ui.newTaskList(areachairInvitations, areachairTagInvitations, tasksOptions);
  $('.tabs-container a[href="#areachair-tasks"]').parent().show();
}

var renderTableAndTasks = function(fetchedData) {
  renderTasks(fetchedData.invitations, fetchedData.tagInvitations);

  renderStatusTable(
    fetchedData.profiles,
    fetchedData.blindedNotes,
    fetchedData.officialReviews,
    fetchedData.metaReviews,
    _.cloneDeep(fetchedData.noteToReviewerIds), // Need to clone this dictionary because some values are missing after the first refresh
    '#assigned-papers'
  );

  registerEventHandlers();

  Webfield.ui.done();
}

var buildTableRow = function(note, reviewerIds, completedReviews, metaReview) {
  var cellCheck = { selected: false, noteId: note.id };

  // Paper number cell
  var cell0 = { number: note.number};

  // Note summary cell
  note.content.authors = null;  // Don't display 'Blinded Authors'
  var cell1 = note;

  // Review progress cell
  var reviewObj;
  var combinedObj = {};
  var ratings = [];
  var confidences = [];
  for (var reviewerNum in reviewerIds) {
    var reviewer = reviewerIds[reviewerNum];
    if (reviewerNum in completedReviews) {
      reviewObj = completedReviews[reviewerNum];
      combinedObj[reviewerNum] = {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
        completedReview: true,
        forum: reviewObj.forum,
        note: reviewObj.id,
        rating: reviewObj.rating,
        confidence: reviewObj.confidence,
        reviewLength: reviewObj.content.review.length
      };
      ratings.push(reviewObj.rating);
      confidences.push(reviewObj.confidence);
    } else {
      var forumUrl = 'https://openreview.net/forum?' + $.param({
        id: note.forum,
        noteId: note.id,
        invitationId: getInvitationId(OFFICIAL_REVIEW_NAME, note.number)
      });
      var lastReminderSent = localStorage.getItem(forumUrl + '|' + reviewer.id);
      combinedObj[reviewerNum] = {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
        forumUrl: forumUrl,
        lastReminderSent: lastReminderSent ? new Date(parseInt(lastReminderSent)).toLocaleDateString() : lastReminderSent
      };
    }
  }

  var cell2 = {
    noteId: note.id,
    numSubmittedReviews: Object.keys(completedReviews).length,
    numReviewers: Object.keys(reviewerIds).length,
    reviewers: combinedObj,
    sendReminder: true
  };

  // Rating cell
  var cell3 = {
    averageRating: 'N/A',
    minRating: 'N/A',
    maxRating: 'N/A'
  };
  if (ratings.length) {
    cell3.averageRating = _.round(_.sum(ratings) / ratings.length, 2);
    cell3.minRating = _.min(ratings);
    cell3.maxRating = _.max(ratings);
  }

  // Confidence cell
  var cell4 = {
    averageConfidence: 'N/A',
    minConfidence: 'N/A',
    maxConfidence: 'N/A'
  };
  if (confidences.length) {
    cell4.averageConfidence = _.round(_.sum(confidences) / confidences.length, 2);
    cell4.minConfidence = _.min(confidences);
    cell4.maxConfidence = _.max(confidences);
  }

  // Status cell
  var invitationUrlParams = {
    id: note.forum,
    noteId: note.id,
    invitationId: getInvitationId('Meta_Review', note.number)
  };
  var cell5 = {
    invitationUrl: '/forum?' + $.param(invitationUrlParams)
  };
  if (metaReview) {
    cell5.recommendation = metaReview.content.recommendation;
    cell5.editUrl = '/forum?id=' + note.forum + '&noteId=' + metaReview.id;
  }

  return [cellCheck, cell0, cell1, cell2, cell3, cell4, cell5];
};


// Event Handlers
var registerEventHandlers = function() {
  $('#group-container').on('click', 'a.note-contents-toggle', function(e) {
    var hiddenText = 'Show paper details';
    var visibleText = 'Hide paper details';
    var updated = $(this).text() === hiddenText ? visibleText : hiddenText;
    $(this).text(updated);
  });

  $('#group-container').on('click', 'a.send-reminder-link', function(e) {
    var $link = $(this);
    var userId = $link.data('userId');
    var forumUrl = $link.data('forumUrl');

    var sendReviewerReminderEmails = function(e) {
      var postData = {
        groups: [userId],
        forumUrl: forumUrl,
        subject: $('#message-reviewers-modal input[name="subject"]').val().trim(),
        message: $('#message-reviewers-modal textarea[name="message"]').val().trim(),
      };

      $('#message-reviewers-modal').modal('hide');
      // promptMessage('Your reminder email has been sent to ' + view.prettyId(userId));
      postReviewerEmails(postData);
      $link.after(' (Last sent: ' + (new Date()).toLocaleDateString());

      return false;
    };

    var modalHtml = Handlebars.templates.messageReviewersModal({
      singleRecipient: true,
      reviewerId: userId,
      forumUrl: forumUrl,
      defaultSubject: SHORT_PHRASE + ' Reminder',
      defaultBody: 'This is a reminder to please submit your review for ' + SHORT_PHRASE + '. ' +
        'Click on the link below to go to the review page:\n\n[[SUBMIT_REVIEW_LINK]]' +
        '\n\nThank you,\n' + SHORT_PHRASE + ' Area Chair',
    });
    $('#message-reviewers-modal').remove();
    $('body').append(modalHtml);

    $('#message-reviewers-modal .btn-primary').on('click', sendReviewerReminderEmails);
    $('#message-reviewers-modal form').on('submit', sendReviewerReminderEmails);

    $('#message-reviewers-modal').modal();
    return false;
  });

  $('#group-container').on('click', 'a.collapse-btn', function(e) {
    $(this).next().slideToggle();
    if ($(this).text() === 'Show reviewers') {
      $(this).text('Hide reviewers');
    } else {
      $(this).text('Show reviewers');
    }
    return false;
  });
};

var postReviewerEmails = function(postData) {
  postData.message = postData.message.replace(
    '[[SUBMIT_REVIEW_LINK]]',
    postData.forumUrl
  );

  return Webfield.post('/mail', postData)
    .then(function(response) {
      // Save the timestamp in the local storage
      for (var i = 0; i < postData.groups.length; i++) {
        var userId = postData.groups[i];
        localStorage.setItem(postData.forumUrl + '|' + userId, Date.now());
      }
    });
};

main();
