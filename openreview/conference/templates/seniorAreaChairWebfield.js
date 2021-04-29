// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var CONFERENCE_ID = '';
var SHORT_PHRASE = '';
var BLIND_SUBMISSION_ID = '';
var OFFICIAL_META_REVIEW_NAME = '';
var HEADER = {};
var SENIOR_AREA_CHAIR_NAME = '';
var AREA_CHAIRS_ID = '';
var EMAIL_SENDER = null;



var WILDCARD_INVITATION = CONFERENCE_ID + '.*';
var PAGE_SIZE = 25;

var conferenceStatusData = {};

// Main function is the entry point to the webfield code
var main = function() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID);
  }

  renderHeader();

  loadData()
  .then(formatData)
  .then(renderTableAndTasks)
  .fail(function() {
    Webfield.ui.errorMessage();
  });
};

var renderHeader = function() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);
  Webfield.ui.header(HEADER.title, HEADER.instructions);

  var loadingMessage = '<p class="empty-message">No assigned Area Chairs.</p>';
  var tabsList = [
    {
      heading: 'Assigned Area Chairs',
      id: 'areachair-status',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll',
      active: true
    },
    {
      heading: 'Senior Area Chair Tasks',
      id: 'senior-areachair-tasks',
      content: loadingMessage
    }
  ];

  Webfield.ui.tabPanel(tabsList);
};

var getRootGroups = function() {
  // Get paper groups or assignments

  return $.Deferred().resolve([]);

};

var loadData = function() {

  var assignmentsP = Webfield.getAll('/edges', {
    invitation: 'NeurIPS.cc/2021/Conference/Senior_Area_Chairs/-/Proposed_Assignment',
    tail: user.profile.id
  });

  var submissionsP = Webfield.getAll('/notes', {
    invitation: BLIND_SUBMISSION_ID,
    details: 'invitation,tags,original,replyCount',
    sort: 'number:asc'
  });

  var invitationsP = Webfield.getAll('/invitations', {
    regex: WILDCARD_INVITATION,
    invitee: true,
    duedate: true,
    type: 'all',
    details: 'replytoNote,repliedNotes,repliedTags,repliedEdges'
  })
  .then(function(invitations) {
    return _.filter(invitations, function(inv) {
      return _.get(inv, 'reply.replyto') || _.get(inv, 'reply.referent') || _.has(inv, 'reply.content.head') || _.has(inv, 'reply.content.tag');
    });
  });

  return $.when(
    assignmentsP,
    submissionsP,
    invitationsP
  );
};

var formatData = function(assignmentEdges, submissions, invitations) {
  conferenceStatusData = {
    areaChairs: assignmentEdges.map(function(edge) { return edge.head; }),
    areaChairGroups: { byAreaChairs: {} },
    reviewerGroups: { byNotes: {} },
    assignmentEdges: assignmentEdges,
    submissions: submissions,
    invitations: invitations
  };

  return $.Deferred().resolve(conferenceStatusData);
};

var renderTasks = function(invitations) {
  //  My Tasks tab
  var tasksOptions = {
    container: '#senior-areachair-tasks',
    emptyMessage: 'No outstanding tasks for this conference',
    referrer: encodeURIComponent('[Senior Area Chair Console](/group?id=' + CONFERENCE_ID + '/' + SENIOR_AREA_CHAIR_NAME + '#senior-areachair-tasks)')
  }
  $(tasksOptions.container).empty();

  Webfield.ui.newTaskList(invitations, [], tasksOptions);
  $('.tabs-container a[href="#senior-areachair-tasks"]').parent().show();
}

var renderTableAndTasks = function(conferenceStatusData) {

  displayAreaChairsStatusTable(conferenceStatusData);

  renderTasks(conferenceStatusData.invitations);

  registerEventHandlers();

  Webfield.ui.done();
}

var buildEdgeBrowserUrl = function(startQuery, invGroup, invName) {
  var invitationId = invGroup + '/-/' + invName;
  var referrerUrl = '/group' + location.search + location.hash;
  var conflictInvitation = conferenceStatusData.invitationMap[invGroup + '/-/Conflict'];
  var scoresInvitation = conferenceStatusData.invitationMap[invGroup + '/-/' + SCORES_NAME];

  // Right now this is only showing bids, affinity scores, and conflicts as the
  // other scores invitations + labels are not available in the PC console
  return '/edges/browse' +
    (startQuery ? '?start=' + invitationId + ',' + startQuery + '&' : '?') +
    'traverse=' + invitationId +
    '&browse=' + invitationId +
    (scoresInvitation ? ';' + scoresInvitation.id : '') +
    (conflictInvitation ? ';' + conflictInvitation.id : '') +
    '&referrer=' + encodeURIComponent('[PC Console](' + referrerUrl + ')');
};

var displaySortPanel = function(container, sortOptions, sortResults, searchResults) {
  var searchType = container.substring(1).split('-')[0] + 's';
  var searchBarHtml = _.isFunction(searchResults) ?
    '<strong style="vertical-align: middle;">Search:</strong> ' +
    '<input type="text" class="form-search form-control" class="form-control" placeholder="Search all ' + searchType + '..." ' +
      'style="width: 300px; margin-right: 1.5rem; line-height: 34px;">' :
    '';
  var sortOptionsHtml = _.map(_.keys(sortOptions), function(option) {
    return '<option class="' + option.replace(/_/g, '-') + '-' + container.substring(1) + '" value="' + option + '">' + option.replace(/_/g, ' ') + '</option>';
  });
  var sortDropdownHtml = sortOptionsHtml.length && _.isFunction(sortResults) ?
    '<strong style="vertical-align: middle;">Sort By:</strong> ' +
    '<select class="form-sort form-control" style="width: 250px; line-height: 1rem;">' + sortOptionsHtml + '</select>' +
    '<button class="form-order btn btn-icon"><span class="glyphicon glyphicon-sort"></span></button>' :
    '';

  $(container).html(
    '<form class="form-inline search-form clearfix" role="search">' +
      '<div class="pull-left"></div>' +
      '<div class="pull-right">' +
        searchBarHtml +
        sortDropdownHtml +
      '</div>' +
    '</form>'
  );

  $(container + ' select.form-sort').on('change', function(event) {
    sortResults($(event.target).val(), false);
  });
  $(container + ' .form-order').on('click', function(event) {
    sortResults($(container).find('.form-sort').val(), true);
    return false;
  });
  $(container + ' .form-search').on('keyup', _.debounce(function() {
    var searchText = $(container + ' .form-search').val().toLowerCase().trim();
    searchResults(searchText);
  }, 300));
  $(container + ' form.search-form').on('submit', function() {
    return false;
  });
};

var renderPaginatedTable = function($container, tableData, pageNumber) {
  if (!tableData.rows) {
    tableData.rows = [];
  }

  $container.find('.table-container, .pagination-container').remove();

  var offset = (pageNumber - 1) * PAGE_SIZE;
  var tableHtml = Handlebars.templates['components/table']({
    headings: tableData.headings,
    rows: tableData.rows.slice(offset, offset + PAGE_SIZE),
    extraClasses: tableData.extraClasses
  });

  var paginationHtml = null;
  if (tableData.rows.length > PAGE_SIZE) {
    paginationHtml = view.paginationLinks(tableData.rows.length, PAGE_SIZE, pageNumber);
  }

  $container.append(tableHtml, paginationHtml);

  if (paginationHtml) {
    $('ul.pagination', $container).css({ marginTop: '2.5rem', marginBottom: '0' });
  }
};

var paginationOnClick = function($target, $container, tableData) {
  if ($target.hasClass('disabled') || $target.hasClass('active')) {
    return;
  }

  var pageNum = parseInt($target.data('pageNumber'), 10);
  if (isNaN(pageNum)) {
    return;
  }

  // Only way to get fresh data after doing reviewer re-assignment is to re-compute
  // the whole table
  if (paperStatusNeedsRerender) {
    $('#paper-status').data('lastPageNum', pageNum);
    displayPaperStatusTable();
  } else {
    renderPaginatedTable($container, tableData, pageNum);
  }

  var scrollPos = $container.offset().top - 104;
  $('html, body').animate({scrollTop: scrollPos}, 400);

  $container.data('lastPageNum', pageNum);
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

var postReviewerEmails = function(postData) {
  var formttedData = _.pick(postData, ['groups', 'subject', 'message', 'parentGroup']);
  formttedData.message = postData.message.replace('[[SUBMIT_REVIEW_LINK]]', postData.forumUrl);
  if (EMAIL_SENDER) {
    formttedData.from = EMAIL_SENDER;
  }

  return Webfield.post('/messages', formttedData)
  .then(function() {
    // Save the timestamp in the local storage
    for (var i = 0; i < postData.groups.length; i++) {
      var userId = postData.groups[i];
      localStorage.setItem(postData.forumUrl + '|' + userId, Date.now());
    }
  });
};

var buildSPCTableRow = function(index, areaChair, papers) {

  var acTableeferrerUrl = encodeURIComponent('[Senior Area Chair Console](/group?id=' + CONFERENCE_ID + '/Senior_Area_Chairss#areachair-status)');

  var summary = {
    id: areaChair.id,
    name: areaChair.name,
    email: areaChair.email,
    showBids: !!conferenceStatusData.bidEnabled,
    completedBids: areaChair.bidCount || 0,
    //edgeBrowserBidsUrl: buildEdgeBrowserUrl('tail:' + areaChair.id, AREA_CHAIRS_ID, BID_NAME),
    showRecommendations: !!conferenceStatusData.recommendationEnabled,
    completedRecs: areaChair.acRecommendationCount || 0,
    //edgeBrowserRecsUrl: buildEdgeBrowserUrl('signatory:' + areaChair.id, REVIEWERS_ID, RECOMMENDATION_NAME)
  }

  var numCompletedReviews = 0;
  var numCompletedMetaReviews = 0;
  var paperProgressData = _.map(papers, function(paper) {
    var ratings = [];
    var numOfReviewers = 0;

    for (var reviewerNum in paper.reviewers) {
      if (reviewerNum in paper.reviews) {
        ratings.push(paper.reviews[reviewerNum].rating);
      }
      numOfReviewers++;
    }

    var averageRating = 'N/A';
    var minRating = 'N/A';
    var maxRating = 'N/A';
    if (ratings.length) {
      averageRating = _.round(_.sum(ratings) / ratings.length, 2);
      minRating = _.min(ratings);
      maxRating = _.max(ratings);

      if (ratings.length == numOfReviewers) {
        numCompletedReviews++;
      }
    }

    if (paper.metaReview) {
      numCompletedMetaReviews++;
    }

    return {
      note: paper.note,
      averageRating: averageRating,
      maxRating: maxRating,
      minRating: minRating,
      numOfReviews: ratings.length,
      numOfReviewers: numOfReviewers,
      metaReview: paper.metaReview
    }
  });

  var reviewProgressData = {
    numCompletedMetaReviews: numCompletedMetaReviews,
    numCompletedReviews: numCompletedReviews,
    numPapers: papers.length,
    papers: _.sortBy(paperProgressData, [function(p) { return p.note.number; }]),
    referrer: acTableeferrerUrl
  }

  return {
    summary: summary,
    reviewProgressData: reviewProgressData
  }

};


var displayAreaChairsStatusTable = function(conferenceStatusData) {
  var container = '#areachair-status';
  var notes = conferenceStatusData.submissions;
  var reviewerIds = conferenceStatusData.reviewerGroups.byNotes;
  var areachairIds = conferenceStatusData.areaChairGroups.byAreaChairs;

  var rowData = [];
  _.forEach(conferenceStatusData.areaChairs, function(areaChair, index) {
    var numbers = areachairIds[areaChair];
    var papers = [];
    _.forEach(numbers, function(number) {
      var note = _.find(notes, ['number', parseInt(number)]);
      if (!note) {
        return;
      }

      var reviewers = reviewerIds[number];
      var reviews = []; //get the reviews from direct replies
      var metaReview = _.find(note.details.directReplies, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, number)]);
      papers.push({
        note: note,
        reviewers: reviewers,
        reviews: reviews,
        metaReview: metaReview
      });
    });

    //var areaChairProfile = findProfile(conferenceStatusData.profiles, areaChair);
    rowData.push(buildSPCTableRow(index + 1, { id: areaChair, name: areaChair, email: areaChair }, papers));
  });

  var order = 'asc';
  var sortOptions = {
    Area_Chair: function(row) { return row.summary.name.toLowerCase(); },
    Bids_Completed: function(row) { return row.summary.completedBids },
    Reviewer_Recommendations_Completed: function(row) { return row.summary.completedRecs },
    Papers_Assigned: function(row) { return row.reviewProgressData.numPapers; },
    Papers_with_Completed_Review_Missing: function(row) { return row.reviewProgressData.numPapers - row.reviewProgressData.numCompletedReviews; },
    Papers_with_Completed_Review: function(row) { return row.reviewProgressData.numCompletedReviews; },
    Papers_with_Completed_MetaReview_Missing: function(row) { return row.reviewProgressData.numPapers - row.reviewProgressData.numCompletedMetaReviews; },
    Papers_with_Completed_MetaReview: function(row) { return row.reviewProgressData.numCompletedMetaReviews; }
  };

  var sortResults = function(newOption, switchOrder) {
    $(container + ' .form-search').val('');

    if (switchOrder) {
      order = order === 'asc' ? 'desc' : 'asc';
    }
    rowData = _.orderBy(rowData, sortOptions[newOption], order);
    renderTable(container, rowData);
  }

  var searchResults = function(searchText) {
    $(container).data('lastPageNum', 1);
    $(container + ' .form-sort').val('Area_Chair');

    // Currently only searching on area chair name
    var filterFunc = function(row) {
      return row.summary.name.toLowerCase().indexOf(searchText) !== -1;
    };
    var filteredRows = searchText
      ? _.orderBy(_.filter(rowData, filterFunc), sortOptions['Area_Chair'], 'asc')
      : rowData;
    renderTable(container, filteredRows);
  };

  // Message modal handler
  var sendReviewerReminderEmailsStep1 = function(e) {
    var subject = $('#message-reviewers-modal input[name="subject"]').val().trim();
    var message = $('#message-reviewers-modal textarea[name="message"]').val().trim();
    var filter  = $(this)[0].dataset['filter'];

    var filterFuncs = {
      'msg-no-bids': function(row) {
        return row.summary.completedBids === 0;
      },
      'msg-no-recs': function(row) {
        return row.summary.completedRecs === 0;
      },
      'msg-unsubmitted-reviews': function(row) {
        return row.reviewProgressData.numCompletedReviews < row.reviewProgressData.numPapers;
      },
      'msg-unsubmitted-metareviews': function(row) {
        return row.reviewProgressData.numCompletedMetaReviews < row.reviewProgressData.numPapers;
      },
      'msg-submitted-none-metareviews': function(row) {
        return row.reviewProgressData.numCompletedMetaReviews === 0 && row.reviewProgressData.numPapers;
      }
    }
    var usersToMessage = rowData.filter(filterFuncs[filter]).map(function(row) {
      return {
        id: row.summary.id,
        name: row.summary.name,
        email: row.summary.email
      }
    });
    localStorage.setItem('reviewerMessages', JSON.stringify([{
      groups: _.map(usersToMessage, 'id'),
      subject: subject,
      message: message,
      parentGroup: AREA_CHAIRS_ID
    }]));
    localStorage.setItem('messageCount', usersToMessage.length);

    // Show step 2
    var namesHtml = _.flatMap(usersToMessage, function(obj) {
      var text = obj.name + ' <span>&lt;' + obj.email + '&gt;</span>';
      return text;
    }).join(', ');
    $('#message-reviewers-modal .modal-body > p').html('A total of <span class="num-reviewers"></span> reminder emails will be sent to the following reviewers:');
    $('#message-reviewers-modal .reviewer-list').html(namesHtml);
    $('#message-reviewers-modal .num-reviewers').text(usersToMessage.length);
    $('#message-reviewers-modal .step-1').hide();
    $('#message-reviewers-modal .step-2').show();

    return false;
  };

  var renderTable = function(container, data) {
    var rowData = data.map(function(d, index) {
      var number = '<strong class="note-number">' + (index + 1) + '</strong>';
      var summaryHtml = Handlebars.templates.committeeSummary(d.summary);
      var progressHtml = Handlebars.templates.notesAreaChairProgress(d.reviewProgressData);
      var statusHtml = Handlebars.templates.notesAreaChairStatus(d.reviewProgressData);
      return [number, summaryHtml, progressHtml, statusHtml];
    });

    var $container = $(container);
    var tableData = {
      headings: ['#', 'Area Chair', 'Review Progress', 'Status'],
      rows: rowData,
      extraClasses: 'console-table'
    };
    var pageNum = $container.data('lastPageNum') || 1;
    renderPaginatedTable($container, tableData, pageNum);

    $container.on('click', 'ul.pagination > li > a', function(e) {
      paginationOnClick($(this).parent(), $container, tableData);
      return false;
    });

    $('.message-acs-container li > a', container).off('click').on('click', function(e) {
      var filter = $(this).attr('class');
      $('#message-reviewers-modal').remove();

      var defaultBody = '';

      var modalHtml = Handlebars.templates.messageReviewersModalFewerOptions({
        filter: filter,
        defaultSubject: SHORT_PHRASE + ' Reminder',
        defaultBody: defaultBody,
      });
      $('body').append(modalHtml);
      $('#message-reviewers-modal .modal-body > p').text('Enter a message to be sent to all selected area chairs below. You will have a chance to review a list of all recipients after clicking "Next" below.')

      $('#message-reviewers-modal .btn-primary.step-1').on('click', sendReviewerReminderEmailsStep1);
      $('#message-reviewers-modal .btn-primary.step-2').on('click', sendReviewerReminderEmailsStep2);
      $('#message-reviewers-modal form').on('submit', sendReviewerReminderEmailsStep1);

      $('#message-reviewers-modal').modal();

      if ($('.ac-console-table input.select-note-reviewers:checked').length) {
        $('#message-reviewers-modal select[name="group"]').val('selected');
      }
      return false;
    });
  }

  displaySortPanel(container, sortOptions, sortResults, searchResults);
  $(container).find('form.search-form .pull-left').html(
    '<div class="btn-group message-acs-container" role="group">' +
      '<button type="button" class="message-acs-btn btn btn-icon dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
        '<span class="glyphicon glyphicon-envelope"></span> &nbsp;Message Area Chairs ' +
        '<span class="caret"></span>' +
      '</button>' +
      '<ul class="dropdown-menu">' +
        (conferenceStatusData.bidEnabled ? '<li><a class="msg-no-bids">Area Chairs with 0 bids</a></li>' : '') +
        (conferenceStatusData.recommendationEnabled ? '<li><a class="msg-no-recs">Area Chairs with 0 recommendations</a></li>' : '') +
        '<li><a class="msg-unsubmitted-reviews">Area Chairs with unsubmitted reviews</a></li>' +
        '<li><a class="msg-submitted-none-metareviews">Area Chairs with 0 submitted meta reviews</a></li>' +
        '<li><a class="msg-unsubmitted-metareviews">Area Chairs with unsubmitted meta reviews</a></li>' +
      '</ul>' +
    '</div>'
  );
  renderTable(container, rowData);
};



// Event Handlers
var registerEventHandlers = function() {
};


main();
