// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var CONFERENCE_ID = '';
var SHORT_PHRASE = '';
var BLIND_SUBMISSION_ID = '';
var OFFICIAL_REVIEW_NAME = '';
var REVIEW_RATING_NAME = 'recommendation';
var REVIEW_CONFIDENCE_NAME = 'confidence';
var HEADER = {};
var ETHICS_CHAIRS_NAME = '';
var ETHICS_REVIEWERS_NAME = '';
var ETHICS_CHAIRS_ID = CONFERENCE_ID + '/' + ETHICS_CHAIRS_NAME;
var ETHICS_REVIEWERS_ID = CONFERENCE_ID + '/' + ETHICS_REVIEWERS_NAME;
var WILDCARD_INVITATION = CONFERENCE_ID + '.*';
var PAGE_SIZE = 25;
var EMAIL_SENDER = null;

var singularReviewersName = ETHICS_REVIEWERS_NAME.endsWith('s') ? ETHICS_REVIEWERS_NAME.slice(0, -1) : ETHICS_REVIEWERS_NAME;
var conferenceStatusData = {};
var selectedNotesById = {};

var filterOperators = ['!=','>=','<=','>','<','=']; // sequence matters
var propertiesAllowed = {
    number:['note.number'],
    id:['note.id','summary.id'],// multi tab same prop
    title:['note.content.title'],
    author:['note.content.authors','note.content.authorids'], // multi props
    keywords:['note.content.keywords'],
    reviewer:['reviewProgressData.reviewers'],
    numReviewersAssigned:['reviewProgressData.numReviewers'],
    numReviewsDone:['reviewProgressData.numSubmittedReviews'],
    replyCount:['reviewProgressData.forumReplyCount']
}

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

  var loadingMessage = '<p class="empty-message">No information to display at this time.</p>';
  var tabsList = [
    {
      heading: 'Overview',
      id: 'overview',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll',
      active: true
    },
    {
      heading: 'Paper Status',
      id: 'paper-status',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll'
    },
    {
      heading: 'Ethics Chair Tasks',
      id: 'ethic-review-chair-tasks',
      content: loadingMessage
    }
  ];

  Webfield.ui.tabPanel(tabsList);
};

var getGroups = function() {
    return Webfield.getAll('/groups', {
      id: CONFERENCE_ID + '/Paper.*',
      select: 'id,members'
    }).then(function(groups) {
      var reviewerGroups = [];
      var anonReviewerGroups = [];
      var areaChairGroups = [];
      var anonAreaChairGroups = [];
      var seniorAreaChairGroups = [];
      for (var groupIdx = 0; groupIdx < groups.length; groupIdx++) {
        var group = groups[groupIdx];
        if (group.id.endsWith('/' + ETHICS_REVIEWERS_NAME)) {
          reviewerGroups.push(group);
        } else if (_.includes(group.id, '/' + singularReviewersName + '_')) {
          anonReviewerGroups.push(group);
        } else if (group.id.endsWith('/Area_Chairs')) {
          areaChairGroups.push(group);
        } else if (_.includes(group.id, 'Area_Chair_')) {
          anonAreaChairGroups.push(group);
        } else if (group.id.endsWith('/Senior_Area_Chairs')) {
          seniorAreaChairGroups.push(group);
        }
      }
      return {
        anonReviewerGroups: anonReviewerGroups,
        reviewerGroups: reviewerGroups,
        anonAreaChairGroups: anonAreaChairGroups,
        areaChairGroups: areaChairGroups,
        seniorAreaChairGroups: seniorAreaChairGroups
      };
    });
  };

var loadData = function(papers) {

  var recruitmentGroupsP = Webfield.getAll('/groups', {
    regex: CONFERENCE_ID + '/' + ETHICS_REVIEWERS_NAME + '.*'
  })

  var submissionsP = Webfield.getAll('/notes', {
    invitation: BLIND_SUBMISSION_ID,
    details: 'invitation,tags,original,replyCount,directReplies',
    sort: 'number:asc'
  });

  return $.when(
    getGroups(),
    submissionsP,
    getAllInvitations(),
    recruitmentGroupsP
  );
};

// Util functions
var getNumberfromGroup = function(groupId, name) {
  var tokens = groupId.split('/');
  var paper = _.find(tokens, function(token) {
    return _.startsWith(token, name);
  });

  return paper ? paper.replace(name, '') : null;
};

var getPaperNumbersfromGroups = function(groups) {
  return _.map(groups, function(group) {
    return parseInt(getNumberfromGroup(group.id, 'Paper'));
  });
};

var getInvitationId = function(name, number) {
  return CONFERENCE_ID + '/Paper' + number + '/-/' + name;
};

var findProfile = function(id) {
  if (conferenceStatusData.profiles[id]) {
    return conferenceStatusData.profiles[id];
  }
  var profile = _.find(conferenceStatusData.profiles, function(p) {
    return _.includes(p.allNames, id) || _.includes(p.allEmails, id);
  });
  return profile || {
    id: id,
    name: id.indexOf('~') === 0 ? view.prettyId(id) : id,
    email: id,
    allEmails: [id],
    allNames: [id]
  }
};

var buildNoteMap = function(noteNumbers) {
  var noteMap = Object.create(null);
  for (var i = 0; i < noteNumbers.length; i++) {
    noteMap[noteNumbers[i]] = Object.create(null);
  }
  return noteMap;
};

var buildReviewerGroupMaps = function(noteNumbers, reviewerGroups, anonReviewerGroups) {
  var noteMap = buildNoteMap(noteNumbers);
  var reviewerMap = {};
  var profileIds = [];

  reviewerGroups.forEach(function(g) {
    var num = getNumberfromGroup(g.id, 'Paper');

    if(num in noteMap) {
      g.members.forEach(function(member, index) {
        var anonGroup = anonReviewerGroups.find(function(grp) {
          return grp.id.startsWith(CONFERENCE_ID + '/Paper' + num + '/' + singularReviewersName + '_') && grp.members.length && grp.members[0] == member;
        });
        if (anonGroup) {
          var anonId = getNumberfromGroup(anonGroup.id, singularReviewersName + '_')
          noteMap[num][anonId] = member;
          if (!(member in reviewerMap)) {
            reviewerMap[member] = [];
          }
          reviewerMap[member].push(num);
          profileIds.push(member);
        }
      })
    }
  });

  return {
    byNotes: noteMap,
    byReviewers: reviewerMap,
    profileIds: profileIds
  };
};

var getOfficialReviews = function(notes) {
  var ratingExp = /^(\d+): .*/;

  var reviewByAnonId = {};

  _.forEach(notes, function(n) {
    var anonId = getNumberfromGroup(n.signatures[0], singularReviewersName + '_');
    // Need to parse rating and confidence strings into ints
    ratingNumber = n.content[REVIEW_RATING_NAME] ? n.content[REVIEW_RATING_NAME].substring(0, n.content[REVIEW_RATING_NAME].indexOf(':')) : null;
    n.rating = ratingNumber ? parseInt(ratingNumber, 10) : null;
    confidenceMatch = n.content[REVIEW_CONFIDENCE_NAME] && n.content[REVIEW_CONFIDENCE_NAME].match(ratingExp);
    n.confidence = confidenceMatch ? parseInt(confidenceMatch[1], 10) : null;
    reviewByAnonId[anonId] = n;
  });

  return reviewByAnonId;
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
      profile.name = _.isEmpty(name) ? view.prettyId(profile.id) : name.fullname;
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

var getAllInvitations = function() {

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

  var filterInvitee = function(inv) {
    return _.some(inv.invitees, function(invitee) { return invitee.indexOf(ETHICS_CHAIRS_NAME) !== -1; });
  };

  return $.when(
    invitationsP,
    edgeInvitationsP,
    tagInvitationsP
  ).then(function(noteInvitations, edgeInvitations, tagInvitations) {
    var invitations = noteInvitations.concat(edgeInvitations).concat(tagInvitations);
    return _.filter(invitations, filterInvitee);
  });
};

var formatData = function(groups, submissions, invitations, recruitmentGroups) {

  var noteNumbers = getPaperNumbersfromGroups(groups.reviewerGroups);
  submissions = submissions.filter(function(s) { return noteNumbers.indexOf(s.number) >= 0; });
  var reviewerGroupMaps = buildReviewerGroupMaps(noteNumbers, groups.reviewerGroups, groups.anonReviewerGroups);
  var allProfileIds = _.uniq(reviewerGroupMaps.profileIds);

  return getUserProfiles(allProfileIds)
  .then(function(profiles) {
    submissions.forEach(function(submission) {
      selectedNotesById[submission.id] = false;
      submission.details.reviews = getOfficialReviews(_.filter(submission.details.directReplies, ['invitation', getInvitationId(OFFICIAL_REVIEW_NAME, submission.number)]));
      submission.details.reviewers = reviewerGroupMaps.byNotes[submission.number];
    })

    conferenceStatusData = {
      profiles: profiles,
      reviewerGroups: reviewerGroupMaps,
      submissions: submissions,
      invitations: invitations,
      recruitmentGroups: recruitmentGroups
    };
  })

};

var renderTasks = function(invitations) {
  //  My Tasks tab
  var tasksOptions = {
    container: '#ethics-chair-tasks',
    emptyMessage: 'No outstanding tasks for this conference',
    referrer: encodeURIComponent('[Ethics Chair Console](/group?id=' + CONFERENCE_ID + '/' + ETHICS_CHAIRS_NAME + '#ethics-chair-tasks)')
  }
  $(tasksOptions.container).empty();

  Webfield.ui.newTaskList(invitations, [], tasksOptions);
  $('.tabs-container a[href="#ethics-chair-tasks"]').parent().show();
}

var renderTableAndTasks = function() {

  displayOverview();
  displayPaperStatusTable();
  renderTasks(conferenceStatusData.invitations);

  Webfield.ui.done();
}

var displayOverview = function() {

  var reviewerGroup = _.find(conferenceStatusData.recruitmentGroups, ['id', CONFERENCE_ID + '/' + ETHICS_REVIEWERS_NAME])
  var invitedReviewerGroup = _.find(conferenceStatusData.recruitmentGroups, ['id', CONFERENCE_ID + '/' + ETHICS_REVIEWERS_NAME + '/Invited'])

  var renderStatContainer = function(title, stat, hint) {
    return '<div class="col-md-4 col-xs-6">' +
      '<h4>' + title + '</h4>' +
      (hint ? '<p class="hint">' + hint + '</p>' : '') + stat +
      '</div>';
  };

  // Conference statistics
  var html = '<div class="row" style="margin-top: .5rem;">';
  html += renderStatContainer(
    'Ethics Reviewer Recruitment:',
    '<h3>' + (reviewerGroup && reviewerGroup.members.length) + ' / ' + (invitedReviewerGroup && invitedReviewerGroup.members.length) + '</h3>',
    'accepted / invited'
  );
  html += '</div>';
  html += '<hr class="spacer" style="margin-bottom: 1rem;">';

  // Official Committee
  html += '<div class="row" style="margin-top: .5rem;">';
  html += '<div class="col-md-4 col-xs-6">'
  html += '<h4>Ethics Review Roles:</h4><ul style="padding-left: 15px">' +
    '<li><a href="/group/info?id=' + ETHICS_CHAIRS_ID + '">' + view.prettyId(ETHICS_CHAIRS_NAME) + '</a></li>';
  html += '<li><a href="/group/info?id=' + ETHICS_REVIEWERS_ID + '">' + view.prettyId(ETHICS_REVIEWERS_NAME) + '</a> (' +
    '<a href="/group/info?id=' + ETHICS_REVIEWERS_ID + '/Invited">Invited</a>, ' +
    '<a href="/group/info?id=' + ETHICS_REVIEWERS_ID + '/Declined">Declined</a>)</li></ul>';
  html += '</div>';
  html += '</div>';

//   html += '<hr class="spacer" style="margin-bottom: 1rem;">';
//   html += '<div class="row" style="margin-top: .5rem;">';
//   html += '<div class="col-md-4 col-xs-6">'
//   html += '<h4>Ethics Review Assignments:</h4>' +
//     '<a href="/assignments?group=' + ETHICS_REVIEWERS_ID + '">See Assignments</a>';
//   html += '</div>';
//   html += '</div>';

  $('#overview').html(html);
};

var buildPaperTableRow = function(note) {

  var paperTableReferrerUrl = encodeURIComponent('[Ethics Chair Console](/group?id=' + CONFERENCE_ID + '/' + ETHICS_CHAIRS_NAME + '#paper-status)');
  var reviewerIds = note.details.reviewers;
  var completedReviews = note.details.reviews;

  // Checkbox for selecting each row
  var cellCheck = { selected: false, noteId: note.id };

  // Build Note Summary Cell
  var cell1 = note;
  cell1.referrer = paperTableReferrerUrl;

  // Build Review Progress Cell
  var reviewObj;
  var combinedObj = {};
  var ratings = [];
  var confidences = [];
  for (var reviewerNum in reviewerIds) {
    var reviewer = findProfile(reviewerIds[reviewerNum]);
    if (reviewerNum in completedReviews || reviewer.id in completedReviews) {
      reviewObj = completedReviews[reviewerNum] || completedReviews[reviewer.id];
      combinedObj[reviewerNum] = _.assign({}, reviewer, {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
        completedReview: true,
        forum: reviewObj.forum,
        note: reviewObj.id,
        rating: reviewObj.rating,
        confidence: reviewObj.confidence,
        reviewLength: reviewObj.content.review && reviewObj.content.review.length,
      });
      ratings.push(reviewObj.rating);
      confidences.push(reviewObj.confidence);
    } else {
      var forumUrl = 'https://openreview.net/forum?' + $.param({
        id: note.forum,
        noteId: note.id,
        invitationId: getInvitationId(OFFICIAL_REVIEW_NAME, note.number)
      });
      var lastReminderSent = localStorage.getItem(forumUrl + '|' + reviewer.id);
      combinedObj[reviewerNum] = _.assign({}, reviewer, {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
        forum: note.forum,
        forumUrl: forumUrl,
        paperNumber: note.number,
        reviewerNumber: reviewerNum,
        lastReminderSent: lastReminderSent ?
          new Date(parseInt(lastReminderSent)).toLocaleDateString() :
          lastReminderSent
      });
    }
  }
  var averageRating = 'N/A';
  var minRating = 'N/A';
  var maxRating = 'N/A';
  if (ratings.length) {
    averageRating = _.round(_.sum(ratings) / ratings.length, 2);
    minRating = _.min(ratings);
    maxRating = _.max(ratings);
  }

  var averageConfidence = 'N/A';
  var minConfidence = 'N/A';
  var maxConfidence = 'N/A';
  if (confidences.length) {
    averageConfidence = _.round(_.sum(confidences) / confidences.length, 2);
    minConfidence = _.min(confidences);
    maxConfidence = _.max(confidences);
  }

  var reviewProgressData = {
    noteId: note.id,
    paperNumber: note.number,
    forumReplyCount: note.details['replyCount'],
    numSubmittedReviews: Object.keys(completedReviews).length,
    numReviewers: Object.keys(reviewerIds).length,
    reviewers: combinedObj,
    sendReminder: true,
    showActivityModal: false,
    expandReviewerList: false,
    enableReviewerReassignment : false,
    referrer: paperTableReferrerUrl,
    actions: [
      {
        name: 'Edit Assignments',
        url: '/edges/browse?start=staticList,type:head,ids:' + note.id +
        '&traverse=' + ETHICS_REVIEWERS_ID + '/-/Assignment' +
        '&edit=' + ETHICS_REVIEWERS_ID + '/-/Assignment' +
        '&browse=' + ETHICS_REVIEWERS_ID + '/-/Affinity_Score' + ';' + ETHICS_REVIEWERS_ID + '/-/Conflict'
      }
    ]
  };

  return {
    cellCheck: cellCheck,
    note: cell1,
    reviewProgressData: reviewProgressData
  }
};

var displayPaperStatusTable = function() {

  var container = '#paper-status';

  var rowData = _.map(conferenceStatusData.submissions, function(submission) {
    return buildPaperTableRow(submission);
  });
  var filteredRows = null;
  var toNumber = function(value) {
    return value === 'N/A' ? 0 : value;
  }
  var order = 'desc';
  var sortOptions = {
    Paper_Number: function(row) { return row.note.number; },
    Paper_Title: function(row) { return _.trim(row.note.content.title).toLowerCase(); },
    Reviewers_Assigned: function(row) { return row.reviewProgressData.numReviewers; },
    Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
    Reviews_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedReviews; },
    Number_of_Forum_Replies: function(row) { return row.reviewProgressData.forumReplyCount; },
  };

  var sortResults = function(newOption, switchOrder) {
    if (switchOrder) {
      order = order === 'asc' ? 'desc' : 'asc';
    }
    var rowDataToRender = _.orderBy(filteredRows === null ? rowData : filteredRows, sortOptions[newOption], order);
    renderTable(container, rowDataToRender);
  };

  var searchResults = function(searchText, isQueryMode) {
    $(container).data('lastPageNum', 1);
    $(container + ' .form-sort').val('Paper_Number');

    // Currently only searching on note number and note title
    var filterFunc = function(row) {
      return (
        (row.note.number + '').indexOf(searchText) === 0 ||
        row.note.content.title.toLowerCase().indexOf(searchText) !== -1
      );
    };

    if (searchText) {
        if (isQueryMode) {
            var filterResult = Webfield.filterCollections(rowData, searchText.slice(1), filterOperators, propertiesAllowed, 'note.id');
            filteredRows = filterResult.filteredRows;
            queryIsInvalid = filterResult.queryIsInvalid;
            if (queryIsInvalid) $(container + ' .form-search').addClass('invalid-value');
        } else {
            filteredRows = _.filter(rowData, filterFunc);
        }

        filteredRows = _.orderBy(filteredRows, sortOptions['Paper_Number'], 'asc');
        matchingNoteIds = filteredRows.map(function (row) {
            return row.note.id;
        });
        order = 'asc'
    } else {
        filteredRows = rowData;
        matchingNoteIds = [];
    }
    if (rowData.length !== filteredRows.length) {
        conferenceStatusData.filteredRows = filteredRows
      }
    renderTable(container, filteredRows);
  };

  var renderTable = function(container, data) {
    var paperNumbers = [];
    var rowData = _.map(data, function(d) {
      paperNumbers.push(d.note.number);

      var numberHtml = '<strong class="note-number">' + d.note.number + '</strong>';
      var numberHtml = '<strong class="note-number">' + d.note.number + '</strong>';
      var summaryHtml = Handlebars.templates.noteSummary(d.note);
      var reviewHtml = Handlebars.templates.noteReviewers(d.reviewProgressData);

      var rows = [numberHtml, summaryHtml, reviewHtml];
      return rows;
    });

    var headings = ['#', 'Paper Summary', 'Ethics Review Progress'];

    var $container = $(container);
    var tableData = {
      headings: headings,
      rows: rowData,
      extraClasses: 'console-table paper-table'
    };
    var pageNum = $container.data('lastPageNum') || 1;
    renderPaginatedTable($container, tableData, pageNum);
    postRenderTable(data, pageNum);

    $container.off('click', 'ul.pagination > li > a').on('click', 'ul.pagination > li > a', function(e) {
      paginationOnClick($(this).parent(), $container, tableData);

      var newPageNum = parseInt($(this).parent().data('pageNumber'), 10);
      postRenderTable(data, newPageNum);
      return false;
    });


  };

  var postRenderTable = function(data, pageNum) {
    $('#paper-status .console-table th').eq(0).css('width', '5%');
    $('#paper-status .console-table th').eq(1).css('width', '50%');
    $('#paper-status .console-table th').eq(2).css('width', '45%');

    var offset = (pageNum - 1) * PAGE_SIZE;
    var pageData = data.slice(offset, offset + PAGE_SIZE);

    $(container + ' .console-table > tbody > tr .select-note-reviewers').each(function() {
      var noteId = $(this).data('noteId');
      $(this).prop('checked', selectedNotesById[noteId]);
    });

    var allSelected = _.every(Object.values(selectedNotesById));
    $(container + ' .console-table #select-all-papers').prop('checked', allSelected);
  };

  if (rowData.length) {
    displaySortPanel(container, sortOptions, sortResults, searchResults, true);
    renderTable(container, rowData);
  } else {
    $(container).empty().append('<p class="empty-message">No papers have been submitted. ' +
      'Check back later or contact info@openreview.net if you believe this to be an error.</p>');
  }
  paperStatusNeedsRerender = false;

};

var displaySortPanel = function(container, sortOptions, sortResults, searchResults, enableQuery) {
  var searchType = container.substring(1).split('-')[0] + 's';
  var placeHolder = enableQuery ? 'Enter search term or type + to start a query and press enter' : 'Search all ' + searchType + '...'
  var searchBarWidth = enableQuery ? '440px' : '300px'
  var searchBarHtml = _.isFunction(searchResults) ?
    '<strong style="vertical-align: middle;">Search:</strong> ' +
    '<input type="text" class="form-search form-control" class="form-control" placeholder="' + placeHolder + '" ' +
      'style="width: ' + searchBarWidth + '; margin-right: 1.5rem; line-height: 34px;">' :
    '';
  var sortOptionsHtml = _.map(_.keys(sortOptions), function(option) {
    return '<option class="' + option.replace(/_/g, '-') + '-' + container.substring(1) + '" value="' + option + '">' + option.replace(/_/g, ' ') + '</option>';
  });
  var sortDropdownHtml = sortOptionsHtml.length && _.isFunction(sortResults) ?
    '<strong style="vertical-align: middle;">Sort By:</strong> ' +
    '<select class="form-sort form-control" style="width: 250px; line-height: 1rem;">' + sortOptionsHtml + '</select>' +
    '<button class="form-order btn btn-icon" type="button"><span class="glyphicon glyphicon-sort"></span></button>' :
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
  $(container + ' .form-search').on('keyup', function (e) {
    var searchText = $(container + ' .form-search').val().trim();
    var searchLabel = $(container + ' .form-search').prevAll('strong:first').text();
    if (enableQuery){
      conferenceStatusData.filteredRows = null
    }
    $(container + ' .form-search').removeClass('invalid-value');

    if (enableQuery && searchText.startsWith('+')) {
      // filter query mode
      if (searchLabel === 'Search:') {
        $(container + ' .form-search').prevAll('strong:first').text('Query:');
        $(container + ' .form-search').prevAll('strong:first').after($('<span/>', {
          class: 'glyphicon glyphicon-info-sign'
        }).hover(function (e) {
          $(e.target).tooltip({
            title: "<strong class='tooltip-title'>Query Mode Help</strong>\n<p>In Query mode, you can enter an expression and hit ENTER to search.<br/> The expression consists of property of a paper and a value you would like to search.</p><p>e.g. +number=5 will return the paper 5</p><p>Expressions may also be combined with AND/OR.<br>e.g. +number=5 OR number=6 OR number=7 will return paper 5,6 and 7.<br>If the value has multiple words, it should be enclosed in double quotes.<br>e.g. +title=\"some title to search\"</p><p>Braces can be used to organize expressions.<br>e.g. +number=1 OR ((number=5 AND number=7) OR number=8) will return paper 1 and 8.</p><p>Operators available:".concat(filterOperators.join(', '), "</p><p>Properties available:").concat(Object.keys(propertiesAllowed).join(', '), "</p>"),
            html: true,
            placement: 'bottom'
          });
        }));
      }

      if (e.key === 'Enter') {
        searchResults(searchText, true);
      }
    } else {
      if (enableQuery && searchLabel !== 'Search:') {
        $(container + ' .form-search').prev().remove(); // remove info icon

        $(container + ' .form-search').prev().text('Search:');
      }

      _.debounce(function () {
        searchResults(searchText.toLowerCase(), false);
      }, 300)();
    }
  });
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
    postReviewerEmails(postData);
    promptMessage('A reminder email has been sent to ' + view.prettyId(userId), { overlay: true });
    $link.after(' (Last sent: ' + (new Date()).toLocaleDateString() + ')');

    return false;
  };

  var modalHtml = Handlebars.templates.messageReviewersModalFewerOptions({
    singleRecipient: true,
    reviewerId: userId,
    forumUrl: forumUrl,
    defaultSubject: SHORT_PHRASE + ' Reminder',
    defaultBody: 'This is a reminder to please submit your ethics review for ' + SHORT_PHRASE + '. ' +
      'Click on the link below to go to the review page:\n\n[[SUBMIT_REVIEW_LINK]]' +
      '\n\nThank you,\n' + SHORT_PHRASE + ' ' + view.prettyId(ETHICS_CHAIRS_NAME),
  });
  $('#message-reviewers-modal').remove();
  $('body').append(modalHtml);

  $('#message-reviewers-modal .btn-primary').on('click', sendReviewerReminderEmails);
  $('#message-reviewers-modal form').on('submit', sendReviewerReminderEmails);

  $('#message-reviewers-modal').modal();
  return false;
});


main();
