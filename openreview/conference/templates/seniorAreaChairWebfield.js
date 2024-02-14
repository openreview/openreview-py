// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var CONFERENCE_ID = '';
var SHORT_PHRASE = '';
var BLIND_SUBMISSION_ID = '';
var OFFICIAL_REVIEW_NAME = '';
var REVIEW_RATING_NAME = 'rating';
var REVIEW_CONFIDENCE_NAME = 'confidence';
var OFFICIAL_META_REVIEW_NAME = '';
var DECISION_NAME = '';
var HEADER = {};
var SENIOR_AREA_CHAIR_NAME = '';
var AREA_CHAIRS_ID = '';
var REVIEWERS_ID = '';
var ASSIGNMENT_INVITATION = CONFERENCE_ID + '/' + SENIOR_AREA_CHAIR_NAME + '/-/Assignment';
var ASSIGNMENT_LABEL = null;
var EMAIL_SENDER = null;



var WILDCARD_INVITATION = CONFERENCE_ID + '.*';
var PAGE_SIZE = 25;

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
    areaChair:['areachairProgressData.areachair.name'],
    ratingAvg:['reviewProgressData.averageRating'],
    ratingMax:['reviewProgressData.maxRating'],
    ratingMin:['reviewProgressData.minRating'],
    confidenceAvg:['reviewProgressData.averageConfidence'],
    confidenceMax:['reviewProgressData.maxConfidence'],
    confidenceMin:['reviewProgressData.minConfidence'],
    replyCount:['reviewProgressData.forumReplyCount']
}

// Page State
var conferenceStatusData = {};
var selectedNotesById = {};
var matchingNoteIds = [];

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
      heading: 'Paper Status',
      id: 'paper-status',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll'
    },
    {
      heading: 'Area Chair Status',
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
      if (group.id.endsWith('Reviewers')) {
        reviewerGroups.push(group);
      } else if (_.includes(group.id, 'Reviewer_')) {
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

var loadData = function() {

  var assignmentsP = $.Deferred().resolve([]);
  if (ASSIGNMENT_INVITATION) {
    assignmentsP = Webfield.getAll('/edges', {
      invitation: ASSIGNMENT_INVITATION,
      label: ASSIGNMENT_LABEL,
      tail: user.profile.id
    });
  }

  var submissionsP = Webfield.getAll('/notes', {
    invitation: BLIND_SUBMISSION_ID,
    details: 'invitation,tags,original,replyCount,directReplies',
    sort: 'number:asc'
  });

  return $.when(
    getGroups(),
    assignmentsP,
    submissionsP,
    getAllInvitations()
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
          return grp.id.startsWith(CONFERENCE_ID + '/Paper' + num + '/Reviewer_') && grp.members.length && grp.members[0] == member;
        });
        if (anonGroup) {
          var anonId = getNumberfromGroup(anonGroup.id, 'Reviewer_')
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

var buildAreaChairGroupMaps = function(noteNumbers, areaChairGroups, anonAreaChairGroups) {
  var noteMap = buildNoteMap(noteNumbers);
  var areaChairMap = {};
  var profileIds = [];

  areaChairGroups.forEach(function(g) {
    var num = getNumberfromGroup(g.id, 'Paper');
    if (num in noteMap) {
      g.members.forEach(function(member, index) {
        var anonGroup = anonAreaChairGroups.find(function(grp) {
          return grp.id.startsWith(CONFERENCE_ID + '/Paper' + num + '/Area_Chair_') && grp.members.length && grp.members[0] == member;
        });
        if (anonGroup) {
          var anonId = getNumberfromGroup(anonGroup.id, 'Area_Chair_')
          noteMap[num][anonId] = member;
          if (!(member in areaChairMap)) {
            areaChairMap[member] = [];
          }
          areaChairMap[member].push(num);
          profileIds.push(member);
        }
      })
    }
  });

  return {
    byNotes: noteMap,
    byAreaChairs: areaChairMap,
    profileIds: profileIds
  };
};

var buildSeniorAreaChairGroupMaps = function(noteNumbers, seniorAreaChairGroups) {
  var noteMap = buildNoteMap(noteNumbers);
  var seniorAreaChairMap = {};

  seniorAreaChairGroups.forEach(function(g) {
    var num = getNumberfromGroup(g.id, 'Paper');
    if (num in noteMap) {
      g.members.forEach(function(member, index) {
        noteMap[num] = member;
        if (!(member in seniorAreaChairMap)) {
          seniorAreaChairMap[member] = [];
        }
        seniorAreaChairMap[member].push(num);
      })
    }
  });

  return {
    byNotes: noteMap,
    bySeniorAreaChairs: seniorAreaChairMap
  };
};

var getOfficialReviews = function(notes) {
  var ratingExp = /^(\d+): .*/;

  var reviewByAnonId = {};

  _.forEach(notes, function(n) {
    var anonId = getNumberfromGroup(n.signatures[0], 'Reviewer_');
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
    return _.some(inv.invitees, function(invitee) { return invitee.indexOf(SENIOR_AREA_CHAIR_NAME) !== -1; });
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

var formatData = function(groups, assignmentEdges, submissions, invitations) {

  var noteNumbers = getPaperNumbersfromGroups(groups.seniorAreaChairGroups);
  submissions = submissions.filter(function(s) { return noteNumbers.indexOf(s.number) >= 0; });
  var areaChairGroupMaps = buildAreaChairGroupMaps(noteNumbers, groups.areaChairGroups, groups.anonAreaChairGroups);
  var reviewerGroupMaps = buildReviewerGroupMaps(noteNumbers, groups.reviewerGroups, groups.anonReviewerGroups);

  var areaChairs = assignmentEdges.map(function(edge) { return edge.head; });

  var allProfileIds = _.uniq(areaChairs.concat(reviewerGroupMaps.profileIds).concat(areaChairGroupMaps.profileIds));

  return getUserProfiles(allProfileIds)
  .then(function(profiles) {
    submissions.forEach(function(submission) {
      selectedNotesById[submission.id] = false;
      submission.details.reviews = getOfficialReviews(_.filter(submission.details.directReplies, ['invitation', getInvitationId(OFFICIAL_REVIEW_NAME, submission.number)]));
      submission.details.metaReview = _.find(submission.details.directReplies, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, submission.number)]);
      submission.details.decision = _.find(submission.details.directReplies, ['invitation', getInvitationId(DECISION_NAME, submission.number)]);
      submission.details.reviewers = reviewerGroupMaps.byNotes[submission.number];
      submission.details.areaChairs = areaChairGroupMaps.byNotes[submission.number];
    })

    conferenceStatusData = {
      profiles: profiles,
      areaChairs: areaChairs,
      areaChairGroups: areaChairGroupMaps,
      reviewerGroups: reviewerGroupMaps,
      assignmentEdges: assignmentEdges,
      submissions: submissions,
      invitations: invitations
    };
  })
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

var renderTableAndTasks = function() {

  displayPaperStatusTable();
  displayAreaChairsStatusTable();

  registerEventHandlers();

  Webfield.ui.done();
}

var buildEdgeBrowserUrl = function(startQuery, invGroup, invName) {
  var invitationId = invGroup + '/-/' + invName;
  var referrerUrl = '/group' + location.search + location.hash;

  return '/edges/browse' +
    (startQuery ? '?start=' + AREA_CHAIRS_ID + '/-/' + invName + ',' + startQuery + '&' : '?') +
    'traverse=' + invitationId +
    '&edit=' + invitationId + ';' + invGroup + '/-/Invite_Assignment' +
    '&browse=' + invitationId +
    ';' + invGroup + '/-/Affinity_Score' +
    ';' + invGroup + '/-/Bid' +
    ';' + invGroup + '/-/Custom_Max_Papers,head:ignore' +
    '&hide=' + invGroup + '/-/Conflict' +
    '&maxColumns=2' +
    '&referrer=' + encodeURIComponent('[Senior Area Chair Console](' + referrerUrl + ')');
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
    paginationHtml = view.paginationLinks(tableData.rows.length, PAGE_SIZE, pageNumber, null, { showCount: true });
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

var buildSPCTableRow = function(areaChair, papers) {

  var acTableeferrerUrl = encodeURIComponent('[Senior Area Chair Console](/group?id=' + CONFERENCE_ID + '/Senior_Area_Chairs#areachair-status)');

  var summary = {
    id: areaChair.id,
    name: areaChair.name,
    email: areaChair.email,
    showBids: !!conferenceStatusData.bidEnabled,
    completedBids: areaChair.bidCount || 0,
    edgeBrowserAssignmentUrl: buildEdgeBrowserUrl('tail:' + areaChair.id, REVIEWERS_ID, 'Assignment'),
    showRecommendations: !!conferenceStatusData.recommendationEnabled,
    completedRecs: areaChair.acRecommendationCount || 0,
    //edgeBrowserRecsUrl: buildEdgeBrowserUrl('signatory:' + areaChair.id, REVIEWERS_ID, RECOMMENDATION_NAME)
  }

  var numCompletedReviews = 0;
  var numCompletedMetaReviews = 0;
  var paperProgressData = _.map(papers, function(paper) {
    var ratings = [];
    var numOfReviewers = 0;

    for (var reviewerNum in paper.details.reviewers) {
      if (reviewerNum in paper.details.reviews) {
        ratings.push(paper.details.reviews[reviewerNum].rating);
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

    if (paper.details.metaReview) {
      numCompletedMetaReviews++;
    }

    return {
      note: paper,
      averageRating: averageRating,
      maxRating: maxRating,
      minRating: minRating,
      numOfReviews: ratings.length,
      numOfReviewers: numOfReviewers,
      metaReview: paper.details.metaReview
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


var displayAreaChairsStatusTable = function() {
  var container = '#areachair-status';
  var notes = conferenceStatusData.submissions;
  var areachairIds = conferenceStatusData.areaChairGroups.byAreaChairs;

  var rowData = [];
  var filteredRows = null;
  _.forEach(conferenceStatusData.areaChairs, function(areaChair, index) {
    var numbers = areachairIds[areaChair];
    var papers = [];
    _.forEach(numbers, function(number) {
      var note = _.find(notes, ['number', parseInt(number)]);
      if (!note) {
        return;
      }

      papers.push(note);
    });

    var areaChairProfile = findProfile(areaChair);
    rowData.push(buildSPCTableRow(areaChairProfile, papers));
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
    if (switchOrder) {
      order = order === 'asc' ? 'desc' : 'asc';
    }
    var rowDataToRender = _.orderBy(filteredRows === null ? rowData : filteredRows, sortOptions[newOption], order);
    renderTable(container, rowDataToRender);
  }

  var searchResults = function(searchText, isQueryMode) {
    $(container).data('lastPageNum', 1);
    $(container + ' .form-sort').val('Area_Chair');

    // Currently only searching on area chair name
    var filterFunc = function(row) {
      return row.summary.name.toLowerCase().indexOf(searchText) !== -1;
    };
    if (searchText) {
        if(isQueryMode){
          var filterResult = Webfield.filterCollections(rowData, searchText.slice(1), filterOperators, propertiesAllowed, 'summary.id')
          filteredRows = filterResult.filteredRows;
          queryIsInvalid = filterResult.queryIsInvalid;
          if(queryIsInvalid) $(container + ' .form-search').addClass('invalid-value')
        } else {
          filteredRows = _.filter(rowData, filterFunc)
        }
        filteredRows = _.orderBy(filteredRows, sortOptions['Area_Chair'], 'asc');
        order = 'asc';
      } else {
        filteredRows = rowData;
      }
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
      //parentGroup: AREA_CHAIRS_ID
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

  displaySortPanel(container, sortOptions, sortResults, searchResults, false);
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

var buildPaperTableRow = function(note) {

  var paperTableReferrerUrl = encodeURIComponent('[Senior Area Chair Console](/group?id=' + CONFERENCE_ID + '/Senior_Area_Chairs#paper-status)');

  var reviewerIds = note.details.reviewers;
  var areachairIds = note.details.areaChairs;
  var completedReviews = note.details.reviews;
  var metaReview = note.details.metaReview;
  var decision = note.details.decision;
  var areachairProfile = [];

  for(var areaChairNum in areachairIds) {
    areachairProfile.push(findProfile(areachairIds[areaChairNum]))
  }

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
        forumUrl: '/forum?' + $.param({
          id: note.forum,
          noteId: note.id,
          invitationId: getInvitationId(OFFICIAL_REVIEW_NAME, note.number)
        }),
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
    averageRating: averageRating,
    maxRating: maxRating,
    minRating: minRating,
    averageConfidence: averageConfidence,
    minConfidence: minConfidence,
    maxConfidence: maxConfidence,
    sendReminder: true,
    showActivityModal: true,
    expandReviewerList: false,
    enableReviewerReassignment : false,
    referrer: paperTableReferrerUrl
  };

  var areaChairNames = { name: 'No Area Chair' };
  if (areachairProfile.length) {
    areaChairNames.name = areachairProfile.map(function(p) { return p.name; }).join(', ');
    areaChairNames.email = areachairProfile.map(function(p) { return p.email; }).join(', ');
  }
  var areachairProgressData = {
    numMetaReview: metaReview ? 'One' : 'No',
    areachair: areaChairNames,
    metaReview: metaReview,
    referrer: paperTableReferrerUrl
  };

  return {
    cellCheck: cellCheck,
    note: cell1,
    reviewProgressData: reviewProgressData,
    areachairProgressData: areachairProgressData,
    decision: decision
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
    Average_Rating: function(row) { return toNumber(row.reviewProgressData.averageRating); },
    Max_Rating: function(row) { return toNumber(row.reviewProgressData.maxRating); },
    Min_Rating: function(row) { return toNumber(row.reviewProgressData.minRating); },
    Rating_Range: function(row) { return toNumber(row.reviewProgressData.maxRating) - toNumber(row.reviewProgressData.minRating); },
    Average_Confidence: function(row) { return toNumber(row.reviewProgressData.averageConfidence); },
    Max_Confidence: function(row) { return toNumber(row.reviewProgressData.maxConfidence); },
    Min_Confidence: function(row) { return toNumber(row.reviewProgressData.minConfidence); },
    Confidence_Range: function(row) { return toNumber(row.reviewProgressData.maxConfidence) - toNumber(row.reviewProgressData.minConfidence); },
    Reviewers_Assigned: function(row) { return row.reviewProgressData.numReviewers; },
    Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
    Reviews_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedReviews; },
    Number_of_Forum_Replies: function(row) { return row.reviewProgressData.forumReplyCount; },
  };
  if (AREA_CHAIRS_ID) {
    sortOptions['Meta_Review_Missing'] = function(row) { return row.areachairProgressData.numMetaReview; }
  }
  sortOptions['Decision'] = function(row) { return row.decision ? row.decision.content.decision : 'No Decision'; }

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

  // Message modal handler
  var sendReviewerReminderEmailsStep1 = function(e) {
    var subject = $('#message-reviewers-modal input[name="subject"]').val().trim();
    var message = $('#message-reviewers-modal textarea[name="message"]').val().trim();
    var filter  = $(this)[0].dataset['filter'];

    var count = 0;
    var reviewerMessages = [];
    var reviewerCounts = Object.create(null);

    rowData.forEach(function(row) {
      if (!selectedNotesById[row.note.forum]) {
        return;
      }

      var reviewers = _.map(row.reviewProgressData.reviewers, function(rev) {
        if (rev && rev.hasOwnProperty('note')) {
          rev['completedReview'] = true;
        }
        return rev;
      });
      var users = Object.values(reviewers);
      if (filter === 'msg-submitted-reviewers') {
        users = users.filter(function(u) {
          return u.completedReview;
        });
      } else if (filter === 'msg-unsubmitted-reviewers') {
        users = users.filter(function(u) {
          return !u.completedReview;
        });
      }
      if (!users.length) {
        return;
      }

      var forumUrl = 'https://openreview.net/forum?' + $.param({
        id: row.note.forum,
        noteId: row.note.id,
        invitationId: getInvitationId(OFFICIAL_REVIEW_NAME, row.note.number)
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

  var renderTable = function(container, data) {
    var paperNumbers = [];
    var rowData = _.map(data, function(d) {
      paperNumbers.push(d.note.number);

      var numberHtml = '<strong class="note-number">' + d.note.number + '</strong>';
      var checked = '<label><input type="checkbox" class="select-note-reviewers" data-note-id="' +
        d.note.id + '" ' + (selectedNotesById[d.note.id] ? 'checked="checked"' : '') + '></label>';
      var numberHtml = '<strong class="note-number">' + d.note.number + '</strong>';
      var summaryHtml = Handlebars.templates.noteSummary(d.note);
      var reviewHtml = Handlebars.templates.noteReviewers(d.reviewProgressData);
      var areachairHtml = Handlebars.templates.noteAreaChairs(d.areachairProgressData);
      var decisionHtml = '<h4>' + (d.decision ? d.decision.content.decision : 'No Decision') + '</h4>';

      var rows = [checked, numberHtml, summaryHtml, reviewHtml];
      if (AREA_CHAIRS_ID) {
        rows.push(areachairHtml);
      }
      rows.push(decisionHtml);
      return rows;
    });

    var headings = ['<input type="checkbox" id="select-all-papers">', '#', 'Paper Summary', 'Review Progress'];
    if (AREA_CHAIRS_ID) {
      headings.push('Status');
    }
    headings.push('Decision');

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

    $('.message-papers-container li > a', container).off('click').on('click', function(e) {
      var filter = $(this).attr('class');
      $('#message-reviewers-modal').remove();

      var defaultBody = '';
      if (filter === 'msg-unsubmitted-reviewers') {
        defaultBody = 'This is a reminder to please submit your review for ' + SHORT_PHRASE + '.\n\n'
      }
      defaultBody += 'Click on the link below to go to the review page:\n\n[[SUBMIT_REVIEW_LINK]]' +
      '\n\nThank you,\n' + SHORT_PHRASE + ' Senior Area Chair';

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
  };

  var postRenderTable = function(data, pageNum) {
    $('#paper-status .console-table th').eq(0).css('width', '3%');
    $('#paper-status .console-table th').eq(1).css('width', '5%');
    $('#paper-status .console-table th').eq(2).css('width', '22%');
    $('#paper-status .console-table th').eq(3).css('width', '30%');
    $('#paper-status .console-table th').eq(4).css('width', '28%');
    $('#paper-status .console-table th').eq(5).css('width', '12%');

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
    $(container).find('form.search-form .pull-left').html('<div class="btn-group message-papers-container" role="group">' +
      '<button type="button" class="message-papers-btn btn btn-icon dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" title="Select papers to message corresponding reviewers" disabled="disabled">' +
        '<span class="glyphicon glyphicon-envelope"></span> &nbsp;Message Reviewers ' +
        '<span class="caret"></span>' +
      '</button>' +
      '<ul class="dropdown-menu">' +
        '<li><a class="msg-all-reviewers">All Reviewers of selected papers</a></li>' +
        '<li><a class="msg-submitted-reviewers">Reviewers of selected papers with submitted reviews</a></li>' +
        '<li><a class="msg-unsubmitted-reviewers">Reviewers of selected papers with unsubmitted reviews</a></li>' +
      '</ul>' +
    '</div>'
    // '<div class="btn-group"><button class="btn btn-export-data" type="button">Export</button></div>'
    );
    renderTable(container, rowData);
  } else {
    $(container).empty().append('<p class="empty-message">No papers have been submitted. ' +
      'Check back later or contact info@openreview.net if you believe this to be an error.</p>');
  }
  paperStatusNeedsRerender = false;

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
      defaultBody: 'This is a reminder to please submit your review for ' + SHORT_PHRASE + '. ' +
        'Click on the link below to go to the review page:\n\n[[SUBMIT_REVIEW_LINK]]' +
        '\n\nThank you,\n' + SHORT_PHRASE + ' Senior Area Chair',
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

    Webfield.get('/notes', { signature: CONFERENCE_ID + '/Paper' + paperNum + '/Reviewer_' + reviewerNum })
      .then(function(response) {
        $('#reviewer-activity-modal .modal-body').empty();
        Webfield.ui.searchResults(response.notes, {
          container: '#reviewer-activity-modal .modal-body',
          openInNewTab: true,
          emptyMessage: 'Reviewer ' + reviewerNum + ' has not posted any comments or reviews yet.'
        });
      });

    return false;
  });

  $('#group-container').on('show.bs.tab', 'ul.nav-tabs li a', function(e) {
    // Don't allow the user to switch tabs until all data is finished loading
    return !$(e.target).parent().hasClass('loading');
  });

  $('#group-container').on('shown.bs.tab', 'ul.nav-tabs li a', function(e) {
    var containerId = $(e.target).attr('href');
    if (containerId === '#paper-status') {
      displayPaperStatusTable();
    } else if (containerId === '#areachair-status') {
      displayAreaChairsStatusTable();
    } else if (containerId === '#senior-areachair-tasks') {
      renderTasks(conferenceStatusData.invitations);
    }

    // Reset select note state
    for (var noteId in selectedNotesById) {
      if (selectedNotesById.hasOwnProperty(noteId)) {
        selectedNotesById[noteId] = false;
      }
    }

    matchingNoteIds = [];
  });

  $('#invitation-container').on('hidden.bs.tab', 'ul.nav-tabs li a', function(e) {
    var containerId = $(e.target).attr('href');
    if (containerId !== '#venue-configuration') {
      Webfield.ui.spinner(containerId, {inline: true});
    }
  });

  $('#group-container').on('change', '#select-all-papers', function(e) {
    var $superCheckBox = $(this);
    var $allPaperCheckBoxes = $('input.select-note-reviewers');
    var $msgReviewerButton = $('.message-papers-btn');

    var isSuperSelected = $superCheckBox.prop('checked');
    if (isSuperSelected) {
      $allPaperCheckBoxes.prop('checked', true);
      $msgReviewerButton.attr('disabled', false);
    } else {
      $allPaperCheckBoxes.prop('checked', false);
      $msgReviewerButton.attr('disabled', true);
    }

    for (var noteId in selectedNotesById) {
      if (selectedNotesById.hasOwnProperty(noteId)) {
        if (isSuperSelected) {
          selectedNotesById[noteId] = !matchingNoteIds.length || _.includes(matchingNoteIds, noteId);
        } else {
          selectedNotesById[noteId] = isSuperSelected;
        }
      }
    }
  });

  $('#group-container').on('change', 'input.select-note-reviewers', function(e) {
    var $superCheckBox = $('#select-all-papers');
    var $msgReviewerButton = $('.message-papers-btn');

    var noteId = $(this).data('noteId');
    var isSelected = $(this).prop('checked');
    selectedNotesById[noteId] = isSelected;

    var totalNumSelected = Object.values(selectedNotesById).reduce(function(numSelected, val) {
      return numSelected + (val ? 1 : 0);
    }, 0)
    if (totalNumSelected) {
      $msgReviewerButton.attr('disabled', false);
      var totalNumNotes = Object.keys(selectedNotesById).length;
      if (totalNumSelected === totalNumNotes) {
        $superCheckBox.prop('checked', true);
      } else {
        $superCheckBox.prop('checked', false);
      }
    } else {
      $msgReviewerButton.attr('disabled', true);
      $superCheckBox.prop('checked', false);
    }
  });
};


main();
