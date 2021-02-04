// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var VENUE_ID = '.TMLR';
var SHORT_PHRASE = 'TMLR';
var HEADER = {};

var SUBMISSION_NAME = 'Author_Submission';
var ACTION_EDITOR_NAME = 'AEs';
var REVIEWER_NAME = 'Reviewers';
var REVIEW_NAME = 'Review';
var DECISION_NAME = 'Decision';
var PAPER_GROUP_STRING = 'Paper';

var PAPER_AE_REGEX = VENUE_ID + '/' + PAPER_GROUP_STRING + '.*/' + ACTION_EDITOR_NAME;
var PAPER_REVIEWER_REGEX = VENUE_ID + '/' + PAPER_GROUP_STRING + '.*/' + REVIEWER_NAME + '/.*';
var WILDCARD_INVITATION = VENUE_ID + '.*';
var SUBMISSION_ID = VENUE_ID + '/-/' + SUBMISSION_NAME;

var conferenceStatusData = {};

$.getScript('https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.2/FileSaver.min.js')

// Main function is the entry point to the webfield code
var main = function() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(VENUE_ID);
  }

  renderHeader();

  getAssignedPapers()
  .then(loadData)
  .then(formatData)
  .then(renderTableAndTasks)
  .fail(function() {
    Webfield.ui.errorMessage();
  });
};


// Util functions
var getAssignedPapers = function() {
  paperNumbers = [];
  return Webfield.get('/groups', {
    member: user.id, regex: PAPER_AE_REGEX
  })
  .then(function(result) {
    return getPaperNumbersfromGroups(result.groups);
  });
};

var findProfile = function(profiles, id) {
  var profile = _.find(profiles, function(p) {
    return _.find(p.content.names, function(n) { return n.username == id; }) || _.includes(p.content.emails, id);
  });
  if (profile) {
    return profile;
  } else {
    return {
      id: id,
      name: '',
      email: id,
      allEmails: [id],
      content: {
        names: [{ username: id }]
      }
    }
  }
};

var getNumberfromGroup = function(groupId, name) {
  var tokens = groupId.split('/');
  var paper = _.find(tokens, function(token) {
    return _.startsWith(token, name);
  });

  if (paper) {
    return parseInt(paper.replace(name, ''), 10);
  } else {
    return null;
  }
};

var getPaperNumbersfromGroups = function(groups) {
  return _.filter(_.map(groups, function(group) {
    return getNumberfromGroup(group.id, PAPER_GROUP_STRING);
  }), _.isInteger);
};

var getInvitationId = function(name, number) {
  return VENUE_ID + '/' + PAPER_GROUP_STRING + number + '/-/' + name;
};

// Ajax functions
var loadData = function(noteNumbers) {
  var submissionsP = $.Deferred().resolve([]);
  var repliesP = $.Deferred().resolve([]);
  var reviewersP = $.Deferred().resolve([]);

  if (noteNumbers.length) {
    var noteNumbersStr = noteNumbers.join(',');

    submissionsP = Webfield.getAll('/notes', {
      invitation: SUBMISSION_ID,
      number: noteNumbersStr,
      sort: 'number:desc'
    });

    var noteNumberRegex = noteNumbers.join('|');
    repliesP = Webfield.getAll('/notes', {
      invitation: '^' + VENUE_ID + '/' + PAPER_GROUP_STRING + '(' + noteNumberRegex + ')/-/(' + REVIEW_NAME + '|' + DECISION_NAME + ')'
    });

    reviewersP = Webfield.getAll('/groups', { regex: PAPER_REVIEWER_REGEX });

  }

  var invitationsP = Webfield.getAll('/invitations', {
    regex: WILDCARD_INVITATION,
    invitee: true,
    duedate: true,
    replyto: true,
    type: 'notes',
    details: 'replytoNote,repliedNotes'
  });

  var edgeInvitationsP = Webfield.getAll('/invitations', {
    regex: WILDCARD_INVITATION,
    invitee: true,
    duedate: true,
    type: 'edges',
    details: 'repliedEdges'
  });

  var tagInvitationsP = Webfield.getAll('/invitations', {
    regex: WILDCARD_INVITATION,
    invitee: true,
    duedate: true,
    type: 'tags',
    details: 'repliedTags'
  });

  return $.when(
    submissionsP,
    repliesP,
    reviewersP,
    invitationsP,
    edgeInvitationsP,
    tagInvitationsP
  );
};

var formatData = function(submissions, replies, reviewers, invitations, edgeInvitations, tagInvitations) {

  var statusMap = {};
  var notesById = {};
  var reviewerIds = [];

  //Initialize map for each submission
  submissions.forEach(function(submission) {
    notesById[submission.id] = submission;
    statusMap[submission.number] = {
      submission: submission,
      reviews: {},
      reviewers: {}
    }
  })

  replies.forEach(function(reply) {
    var submission = notesById[reply.forum];
    if (submission) {
      if (reply.invitation.endsWith(DECISION_NAME)) {
        statusMap[submission.number].decision = reply;
      }
      if (reply.invitation.endsWith(REVIEW_NAME)) {
        statusMap[submission.number].reviews[reply.signatures[0]] = reply;
      }
    }

  })

  reviewers.forEach(function(reviewer) {
    var number = getNumberfromGroup(reviewer.id, PAPER_GROUP_STRING);
    if (number in statusMap) {
      statusMap[number].reviewers[reviewer.id] = reviewer.members[0];
      reviewerIds.push(reviewer.members[0]);
    }
  })

  invitations.forEach(function(invitation) {
    var submission = notesById[invitation.reply.forum];
    if (submission && invitation.id.endsWith('/' + DECISION_NAME)) {
      statusMap[submission.number].decisionInvitation = invitation;
    }
  })

  return getUserProfiles(_.uniq(reviewerIds))
  .then(function(profiles) {

    return {
      submissions: submissions,
      profiles: profiles,
      statusMap: statusMap,
      invitations: invitations,
      edgeInvitations: edgeInvitations,
      tagInvitations: tagInvitations
    };
  });
};

var displayError = function(message) {
  message = message || 'The group data could not be loaded.';
  $('#notes').empty().append('<div class="alert alert-danger"><strong>Error:</strong> ' + message + '</div>');
};

var getUserProfiles = function(userIds) {
  var ids = _.filter(userIds, function(id) { return _.startsWith(id, '~');});
  var emails = _.filter(userIds, function(id) { return id.match(/.+@.+/);});

  var profileSearch = [];
  if (ids.length) {
    profileSearch.push(Webfield.post('/profiles/search', {ids: ids}),);
  }
  if (emails.length) {
    profileSearch.push(Webfield.post('/profiles/search', {emails: emails}));
  }

  return $.when.apply($, profileSearch)
  .then(function() {
    var searchResults = _.toArray(arguments);
    var profileMap = {};
    if (!searchResults) {
      return profileMap;
    }
    var addProfileToMap = function(profile) {
      var name = _.find(profile.content.names, ['preferred', true]) || _.first(profile.content.names);
      profile.name = _.isEmpty(name) ? view.prettyId(profile.id) : name.first + ' ' + name.last;
      profile.email = profile.content.preferredEmail || profile.content.emails[0];
      profile.allEmails = profile.content.emailsConfirmed;
      profileMap[profile.id] = profile;
    };
    _.forEach(searchResults, function(result) {
      _.forEach(result.profiles, addProfileToMap);
    });
    return profileMap;
  })
  .fail(function(error) {
    displayError();
    return null;
  });
};

// Render functions
var renderHeader = function() {
  Webfield.ui.setup('#group-container', VENUE_ID);
  Webfield.ui.header(HEADER.title, HEADER.instructions);

  var loadingMessage = '<p class="empty-message">Loading...</p>';
  var tabsList = [
    {
      heading: 'Assigned Papers',
      id: 'assigned-papers',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll',
      active: true
    },
    {
      heading: 'Action Editor Tasks',
      id: 'action-editor-tasks',
      content: loadingMessage
    }
  ];

  Webfield.ui.tabPanel(tabsList);
};

var renderStatusTable = function(data, container) {
    var rows = _.map(data.submissions, function(submission) {
    return buildTableRow(data.statusMap[submission.number], data.profiles);
  });

  // Sort form handler
  var order = 'desc';
  var sortOptions = {
    Paper_Number: function(row) { return row[1].number; },
    Paper_Title: function(row) { return _.toLower(_.trim(row[2].content.title)); },
    Number_of_Forum_Replies: function(row) { return row[3].forumReplyCount; },
    Number_of_Reviews_Submitted: function(row) { return row[3].numSubmittedReviews; },
    Number_of_Reviews_Missing: function(row) { return row[3].numReviewers - row[3].numSubmittedReviews; },
    Average_Rating: function(row) { return row[3].averageRating === 'N/A' ? 0 : row[3].averageRating; },
    Max_Rating: function(row) { return row[3].maxRating === 'N/A' ? 0 : row[3].maxRating; },
    Min_Rating: function(row) { return row[3].minRating === 'N/A' ? 0 : row[3].minRating; },
    Average_Confidence: function(row) { return row[3].averageConfidence === 'N/A' ? 0 : row[3].averageConfidence; },
    Max_Confidence: function(row) { return row[3].maxConfidence === 'N/A' ? 0 : row[3].maxConfidence; },
    Min_Confidence: function(row) { return row[3].minConfidence === 'N/A' ? 0 : row[3].minConfidence; },
    Decision_Recommendation: function(row) { return row[4].recommendation; }
  };

  var sortResults = function(newOption, switchOrder) {
    if (switchOrder) {
      order = order === 'asc' ? 'desc' : 'asc';
    }
    renderTable(_.orderBy(rows, sortOptions[newOption], order), container);
  }

  // Message modal handler
  var sendReviewerReminderEmailsStep1 = function(e) {
    var subject = $('#message-reviewers-modal input[name="subject"]').val().trim();
    var message = $('#message-reviewers-modal textarea[name="message"]').val().trim();
    var filter  = $(this)[0].dataset['filter'];

    var count = 0;
    var selectedRows = rows;
    var reviewerMessages = [];
    var reviewerCounts = Object.create(null);
    var selectedIds = _.map(
      $('.ac-console-table input.select-note-reviewers:checked'),
      function(checkbox) { return $(checkbox).data('noteId'); }
    );
    selectedRows = rows.filter(function(row) {
      return _.includes(selectedIds, row[2].forum);
    });

    selectedRows.forEach(function(row) {
      var users = _.values(row[3].reviewers);
      if (filter === 'msg-submitted-reviewers') {
        users = users.filter(function(u) {
          return u.completedReview;
        });
      } else if (filter === 'msg-unsubmitted-reviewers') {
        users = users.filter(function(u) {
          return !u.completedReview;
        });
      }

      if (users.length) {
        var forumUrl = 'https://openreview.net/forum?' + $.param({
          id: row[2].forum,
          noteId: row[2].id,
          invitationId: getInvitationId(REVIEW_NAME, row[2].number)
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
      promptError('Could not send emails at this time. Please refresh the page and try again.');
    }
    JSON.parse(reviewerMessages).forEach(postReviewerEmails);

    localStorage.removeItem('reviewerMessages');
    localStorage.removeItem('messageCount');

    $('#message-reviewers-modal').modal('hide');
    promptMessage('Successfully sent ' + messageCount + ' emails');
  };

  var sortOptionHtml = Object.keys(sortOptions).map(function(option) {
    return '<option value="' + option + '">' + option.replace(/_/g, ' ') + '</option>';
  }).join('\n');

  var sortBarHtml = '<form class="form-inline search-form clearfix" role="search">' +
    '<div id="div-msg-reviewers" class="btn-group" role="group">' +
      '<button id="message-reviewers-btn" type="button" class="btn btn-icon dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" title="Select papers to message corresponding reviewers" disabled="disabled">' +
        '<span class="glyphicon glyphicon-envelope"></span> &nbsp;Message Reviewers ' +
        '<span class="caret"></span>' +
      '</button>' +
      '<ul class="dropdown-menu" aria-labelledby="grp-msg-reviewers-btn">' +
        '<li><a id="msg-all-reviewers">All Reviewers of selected papers</a></li>' +
        '<li><a id="msg-submitted-reviewers">Reviewers of selected papers with submitted reviews</a></li>' +
        '<li><a id="msg-unsubmitted-reviewers">Reviewers of selected papers with unsubmitted reviews</a></li>' +
      '</ul>' +
    '</div>' +
    '<div class="btn-group"><button class="btn btn-export-data">Export</button></div>' +
    '<div class="pull-right">' +
      '<strong>Sort By:</strong> ' +
      '<select id="form-sort" class="form-control">' + sortOptionHtml + '</select>' +
      '<button id="form-order" class="btn btn-icon"><span class="glyphicon glyphicon-sort"></span></button>' +
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

  $('#div-msg-reviewers').find('a').on('click', function(e) {
    var filter = $(this)[0].id;
    $('#message-reviewers-modal').remove();

    var defaultBody = '';
    if (filter === 'msg-unsubmitted-reviewers'){
      defaultBody = 'This is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n';
    }
    defaultBody += 'Click on the link below to go to the review page:\n\n[[SUBMIT_REVIEW_LINK]]' +
    '\n\nThank you,\n' + SHORT_PHRASE + ' Area Chair';

    var modalHtml = Handlebars.templates.messageReviewersModalFewerOptions({
      filter: filter,
      defaultSubject: SHORT_PHRASE + ' Reminder',
      defaultBody: defaultBody,
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
    renderTable(rows, container);
  } else {
    $(container).empty().append('<p class="empty-message">No assigned papers. ' +
    'Check back later or contact info@openreview.net if you believe this to be an error.</p>');
  }
};

var renderTable = function(rows, container) {
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
    Handlebars.templates.noteMetaReviewStatus
  ];

  var rowsHtml = rows.map(function(row) {
    return row.map(function(cell, i) {
      return templateFuncs[i](cell);
    });
  });

  var tableHtml = Handlebars.templates['components/table']({
    headings: [
      '<input type="checkbox" id="select-all-papers">', '#', 'Paper Summary',
      'Review Progress', 'Decision Status'
    ],
    rows: rowsHtml,
    extraClasses: 'ac-console-table'
  });

  $('.table-container', container).remove();
  $(container).append(tableHtml);
}

var renderTasks = function(invitations, edgeInvitations, tagInvitations) {
  //  My Tasks tab
  var tasksOptions = {
    container: '#action-editor-tasks',
    emptyMessage: 'No outstanding tasks for this journal',
    referrer: encodeURIComponent('[Action Editor Console](/group?id=' + VENUE_ID + '/' + ACTION_EDITOR_NAME + '#action-editor-tasks)')
  }
  $(tasksOptions.container).empty();

  Webfield.ui.newTaskList(invitations, tagInvitations.concat(edgeInvitations), tasksOptions);
  $('.tabs-container a[href="#action-editor-tasks"]').parent().show();
}

var renderTableAndTasks = function(data) {
  conferenceStatusData = data;
  renderTasks(data.invitations, data.edgeInvitations, data.tagInvitations);

  renderStatusTable(data, '#assigned-papers');

  registerEventHandlers();

  Webfield.ui.done();
}

var buildTableRow = function(submissionStatusMap, profiles) {
  var note = submissionStatusMap.submission;
  var cellCheck = { selected: false, noteId: note.id };
  var referrerUrl = encodeURIComponent('[Action Editor Console](/group?id=' + VENUE_ID + '/' + ACTION_EDITOR_NAME + '#assigned-papers)');

  // Paper number cell
  var cell0 = {
    number: note.number
  };

  // Note summary cell
  var cell1 = note;
  cell1.referrer = referrerUrl;

  // Review progress cell
  var combinedObj = {};
  var index = 1;
  for (var reviewerId in submissionStatusMap.reviewers) {
    var reviewerNumber = reviewerId.split('/').slice(-1)[0];
    var reviewerProfile = findProfile(profiles, submissionStatusMap.reviewers[reviewerId])
    var review = submissionStatusMap.reviews[reviewerId];
    if (review) {
      combinedObj[reviewerNumber] = {
        id: reviewerProfile.id,
        name: reviewerProfile.name,
        email: reviewerProfile.email,
        completedReview: true,
        forum: review.forum,
        note: review.id,
        rating: review.content.recommendation,
        confidence: review.content.confidence,
        reviewLength: review.content.review && review.content.review.length
      };
    } else {
      var forumUrl = 'https://openreview.net/forum?' + $.param({
        id: note.forum,
        noteId: note.id,
        invitationId: getInvitationId(REVIEW_NAME, note.number)
      });
      var lastReminderSent = localStorage.getItem(forumUrl + '|' + reviewerProfile.id);
      combinedObj[reviewerNumber] = {
        id: reviewerProfile.id,
        name: reviewerProfile.name,
        email: reviewerProfile.email,
        forum: note.forum,
        forumUrl: forumUrl,
        lastReminderSent: lastReminderSent ? new Date(parseInt(lastReminderSent)).toLocaleDateString() : lastReminderSent,
        paperNumber: note.number,
        reviewerNumber: reviewerId
      };
    }
    index = index + 1;
  }

  var cell2 = {
    noteId: note.id,
    paperNumber: note.number,
    forumReplyCount: note.details['replyCount'],
    numSubmittedReviews: Object.keys(submissionStatusMap.reviews).length,
    numReviewers: Object.keys(submissionStatusMap.reviewers).length,
    reviewers: combinedObj,
    sendReminder: true,
    showActivityModal: true,
    expandReviewerList: false,
    enableReviewerReassignment : false,
    referrer: referrerUrl
  };

  // Status cell
  var cell3 = {
    noteId: note.id,
    paperNumber: note.number
  };
  if (submissionStatusMap.decision) {
    cell3.recommendation = submissionStatusMap.decision.content.recommendation;
    cell3.editUrl = '/forum?id=' + note.forum + '&noteId=' + submissionStatusMap.decision.id + '&referrer=' + referrerUrl;
  }
  if (submissionStatusMap.decisionInvitation) {
    var invitationUrlParams = {
      id: note.forum,
      noteId: note.id,
      invitationId: getInvitationId(DECISION_NAME, note.number),
      referrer: referrerUrl
    };
    cell3.invitationUrl = '/forum?' + $.param(invitationUrlParams);;
  }

  return [cellCheck, cell0, cell1, cell2, cell3];
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
      promptMessage('A reminder email has been sent to ' + view.prettyId(userId), { overlay: true });
      postReviewerEmails(postData);
      $link.after(' (Last sent: ' + (new Date()).toLocaleDateString() + ')');

      return false;
    };

    var modalHtml = Handlebars.templates.messageReviewersModalFewerOptions({
      singleRecipient: true,
      reviewerId: userId,
      forumUrl: forumUrl,
      defaultSubject: SHORT_PHRASE + ' Reminder',
      defaultBody: 'This is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n' +
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

  $('#group-container').on('click', 'a.show-activity-modal', function(e) {
    var paperNum = $(this).data('paperNum');
    var reviewerNum = $(this).data('reviewerNum');
    var reviewerName = $(this).data('reviewerName');
    var reviewerEmail = $(this).data('reviewerEmail');

    $('#reviewer-activity-modal').remove();

    $('#content').append(Handlebars.templates.genericModal({
      id: 'reviewer-activity-modal',
      showHeader: true,
      title: 'Paper ' + paperNum + ' Reviewer ' + reviewerNum + ' Activity',
      body: Handlebars.templates.spinner({ extraClasses: 'spinner-inline' }),
      showFooter: false,
    }));
    $('#reviewer-activity-modal .modal-header').append(
      '<ul class="list-inline">' +
      '<li><strong>Name:</strong> ' + reviewerName + '</li>' +
      '<li><strong>Email:</strong> ' + reviewerEmail + '</li>' +
      '</ul>'
    );
    $('#reviewer-activity-modal').modal('show');

    Webfield.get('/notes', { signature: VENUE_ID + '/' + PAPER_GROUP_STRING + paperNum + '/' + REVIEWER_NAME + '/' + reviewerNum })
      .then(function(response) {
        $('#reviewer-activity-modal .modal-body').empty();
        Webfield.ui.searchResults(response.notes, {
          container: '#reviewer-activity-modal .modal-body',
          openInNewTab: true,
          emptyMessage: 'Reviewer' + reviewerNum + ' has not posted any comments or reviews yet.'
        });
      });

    return false;
  });

  $('#group-container').on('change', '#select-all-papers', function(e) {
    var $superCheckBox = $(this);
    var $allPaperCheckBoxes = $('input.select-note-reviewers');
    var $msgReviewerButton = $('#message-reviewers-btn');
    if ($superCheckBox[0].checked === true) {
      $allPaperCheckBoxes.prop('checked', true);
      $msgReviewerButton.attr('disabled', false);
    } else {
      $allPaperCheckBoxes.prop('checked', false);
      $msgReviewerButton.attr('disabled', true);
    }
  });

  $('#group-container').on('change', 'input.select-note-reviewers', function(e) {
    var $allPaperCheckBoxes = $('input.select-note-reviewers');
    var $msgReviewerButton = $('#message-reviewers-btn');
    var $superCheckBox = $('#select-all-papers');
    var checkedBoxes = $allPaperCheckBoxes.filter(function(index) {
      return $allPaperCheckBoxes[index].checked === true;
    });
    if (checkedBoxes.length) {
      $msgReviewerButton.attr('disabled', false);
      if (checkedBoxes.length === $allPaperCheckBoxes.length) {
        $superCheckBox.prop('checked', true);
      } else {
        $superCheckBox.prop('checked', false);
      }
    } else {
      $msgReviewerButton.attr('disabled', true);
      $superCheckBox.prop('checked', false);
    }
  });

  var buildCSV = function(){
    var profiles = conferenceStatusData.profiles;
    var notes = conferenceStatusData.blindedNotes;
    var completedReviews = conferenceStatusData.officialReviews;
    var metaReviews = conferenceStatusData.metaReviews;
    var reviewerIds = conferenceStatusData.noteToReviewerIds;
    var reviewerRankingByPaper = conferenceStatusData.reviewerRankingByPaper;
    var acRankingByPaper = conferenceStatusData.acRankingByPaper;

    var rowData = [];
    rowData.push(['number',
    'forum',
    'title',
    'abstract',
    'num reviewers',
    'num submitted reviewers',
    'missing reviewers',
    'min rating',
    'max rating',
    'average rating',
    'min confidence',
    'max confidence',
    'average confidence',
    'ac recommendation'].join(',') + '\n');

    _.forEach(notes, function(note) {
      var revIds = reviewerIds[note.number] || Object.create(null);
      for (var revNumber in revIds) {
        var uId = revIds[revNumber];
        revIds[revNumber] = findProfile(profiles, uId);
      }
      var metaReview = _.find(metaReviews, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, note.number)]);
      var noteCompletedReviews = completedReviews[note.number] || Object.create(null);
      var paperTableRow = buildTableRow(note, revIds, noteCompletedReviews, metaReview, null, acRankingByPaper[note.forum], reviewerRankingByPaper[note.forum] || {});

      var title = paperTableRow[2]['content']['title'].replace(/"/g, '""');
      var abstract = paperTableRow[2]['content']['abstract'].replace(/"/g, '""');
      var reviewersData = _.values(paperTableRow[3]['reviewers']);
      var allReviewers = [];
      var missingReviewers = [];
      reviewersData.forEach(function(r) {
        allReviewers.push(r.id);
        if (!r.completedReview) {
          missingReviewers.push(r.id);
        }
      });

      rowData.push([paperTableRow[1]['number'],
      '"https://openreview.net/forum?id=' + paperTableRow[2]['id'] + '"',
      '"' + title + '"',
      '"' + abstract + '"',
      paperTableRow[3]['numReviewers'],
      paperTableRow[3]['numSubmittedReviews'],
      '"' + missingReviewers.join('|') + '"',
      paperTableRow[3]['minRating'],
      paperTableRow[3]['maxRating'],
      paperTableRow[3]['averageRating'],
      paperTableRow[3]['minConfidence'],
      paperTableRow[3]['maxConfidence'],
      paperTableRow[3]['averageConfidence'],
      metaReview && metaReview.content.recommendation
      ].join(',') + '\n');
    });
    return [rowData.join('')];
  };

  $('#group-container').on('click', 'button.btn.btn-export-data', function(e) {
    var blob = new Blob(buildCSV(), {type: 'text/csv'});
    saveAs(blob, SHORT_PHRASE.replace(/\s/g, '_') + '_' + ACTION_EDITOR_NAME + '_paper_status.csv',);
    return false;
  });
};

var postReviewerEmails = function(postData) {
  postData.message = postData.message.replace(
    '[[SUBMIT_REVIEW_LINK]]',
    postData.forumUrl
  );

  return Webfield.post('/messages', _.pick(postData, ['groups', 'subject', 'message']))
    .then(function(response) {
      // Save the timestamp in the local storage
      for (var i = 0; i < postData.groups.length; i++) {
        var userId = postData.groups[i];
        localStorage.setItem(postData.forumUrl + '|' + userId, Date.now());
      }
    });
};

main();
