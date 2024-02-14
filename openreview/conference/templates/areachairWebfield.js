// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var CONFERENCE_ID = '';
var SHORT_PHRASE = '';
var SUBMISSION_ID = '';
var BLIND_SUBMISSION_ID = '';
var HEADER = {};
var AREA_CHAIR_NAME = '';
var SECONDARY_AREA_CHAIR_NAME = '';
var REVIEWER_NAME = '';
var OFFICIAL_REVIEW_NAME = '';
var REVIEW_RATING_NAME = 'rating';
var REVIEW_CONFIDENCE_NAME = 'confidence';
var OFFICIAL_META_REVIEW_NAME = '';
var META_REVIEW_CONTENT_FIELD = 'recommendation'
var SENIOR_AREA_CHAIRS_ID = '';
var ENABLE_REVIEWER_REASSIGNMENT = false;
var ENABLE_REVIEWER_REASSIGNMENT_TO_OUTSIDE_REVIEWERS = false;

var WILDCARD_INVITATION = CONFERENCE_ID + '.*';
var REVIEWER_GROUP = CONFERENCE_ID + '/' + REVIEWER_NAME;
var REVIEWER_GROUP_WITH_CONFLICT = REVIEWER_GROUP+'/-/Conflict';
var PAPER_RANKING_ID = CONFERENCE_ID + '/' + AREA_CHAIR_NAME + '/-/Paper_Ranking';
var REVIEWER_PAPER_RANKING_ID = REVIEWER_GROUP + '/-/Paper_Ranking';
var AREA_CHAIRS_ID = CONFERENCE_ID + '/' + AREA_CHAIR_NAME;
var ENABLE_EDIT_REVIEWER_ASSIGNMENTS = false;
var REVIEWER_ASSIGNMENT_TITLE = '';
var EDGE_BROWSER_PROPOSED_URL = '/edges/browse?start=' + AREA_CHAIRS_ID + '/-/Assignment,tail:' + user.profile.id + '&' +
'traverse=' + REVIEWER_GROUP + '/-/Proposed_Assignment,label:' + REVIEWER_ASSIGNMENT_TITLE  + '&' +
'edit=' + REVIEWER_GROUP + '/-/Proposed_Assignment,label:' + REVIEWER_ASSIGNMENT_TITLE  + '&' +
'browse=' + REVIEWER_GROUP + '/-/Aggregate_Score,label:' + REVIEWER_ASSIGNMENT_TITLE  + ';' +
            REVIEWER_GROUP + '/-/Affinity_Score;' +
            REVIEWER_GROUP + '/-/Custom_Max_Papers,head:ignore&' +
'hide=' + REVIEWER_GROUP + '/-/Conflict&' +
'maxColumns=2&' +
'referrer=[AC Console](/group?id=' + AREA_CHAIRS_ID + ')';

var EDGE_BROWSER_DEPLOYED_URL = '/edges/browse?start=' + AREA_CHAIRS_ID + '/-/Assignment,tail:' + user.profile.id + '&' +
'traverse=' + REVIEWER_GROUP + '/-/Assignment&' +
'edit=' + REVIEWER_GROUP + '/-/Invite_Assignment&' +
'browse=' + REVIEWER_GROUP + '/-/Affinity_Score;' +
            REVIEWER_GROUP + '/-/Custom_Max_Papers,head:ignore&' +
'hide=' + REVIEWER_GROUP + '/-/Conflict&' +
'maxColumns=2&' +
'referrer=[AC Console](/group?id=' + AREA_CHAIRS_ID + ')';

var EDGE_BROWSER_URL = REVIEWER_ASSIGNMENT_TITLE ? EDGE_BROWSER_PROPOSED_URL : EDGE_BROWSER_DEPLOYED_URL;


var filterOperators = ['!=','>=','<=','>','<','=']; // sequence matters
var propertiesAllowed ={
    number:['note.number'],
    id:['note.id'],
    title:['note.content.title'],
    author:['note.content.authors','note.content.authorids'], // multi props
    keywords:['note.content.keywords'],
    reviewer:['reviewProgressData.reviewers'],
    numReviewersAssigned:['reviewProgressData.numReviewers'],
    numReviewsDone:['reviewProgressData.numSubmittedReviews'],
    ratingAvg:['reviewProgressData.averageRating'],
    ratingMax:['reviewProgressData.maxRating'],
    ratingMin:['reviewProgressData.minRating'],
    confidenceAvg:['reviewProgressData.averageConfidence'],
    confidenceMax:['reviewProgressData.maxConfidence'],
    confidenceMin:['reviewProgressData.minConfidence'],
    replyCount:['reviewProgressData.forumReplyCount'],
    recommendation:['metaReviewData.recommendation'],
    ranking:['metaReviewData.ranking']
}

var reviewerSummaryMap = {};
var conferenceStatusData = {};
var reviewerOptions = [];
var paperAndReviewersWithConflict = {};
var paperRankingInvitation = null;
var showRankings = false;
var availableOptions = [];
var anonids = {};

$.getScript('https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.2/FileSaver.min.js')

// Main function is the entry point to the webfield code
var main = function() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID);
  }

  renderHeader();

  getRootGroups()
  .then(loadData)
  .then(formatData)
  .then(renderTableAndTasks)
  .fail(function() {
    Webfield.ui.errorMessage();
  });
};


// Util functions
var getRootGroups = function() {

  var filterAreaChairGroups = function(group) {
    return group.id.endsWith('/Area_Chairs');
  }

  var filterAnonAreaChairGroups = function(group) {
    return _.includes(group.id, '/Area_Chair_');
  }

  var filterSecondaryAreaChairGroups = function(group) {
    if (!SECONDARY_AREA_CHAIR_NAME) {
      return false;
    }
    return _.includes(group.id, SECONDARY_AREA_CHAIR_NAME);
  }

  var allAreaChairGroupsP = Webfield.getAll('/groups', {
    member: user.id,
    regex: CONFERENCE_ID + '/Paper.*',
    select: 'id' + (SECONDARY_AREA_CHAIR_NAME ? ',members' : '')
  })
  .then(function(groups) {
    var secondaryAreaChairPaperNums = getPaperNumbersfromGroups(_.filter(groups, filterSecondaryAreaChairGroups));
    var areaChairPaperNums = [];
    var areaChairGroups = _.filter(groups, filterAreaChairGroups);
    var anonGroups = _.filter(groups, filterAnonAreaChairGroups);
    var primaryAreaChairs = {};
    areaChairGroups.forEach(function(areaChairGroup) {
      var num = parseInt(getNumberfromGroup(areaChairGroup.id, 'Paper'));
      // Filter out secondary area chairs
      if (!_.includes(secondaryAreaChairPaperNums, num)) {
        var anonGroup = anonGroups.find(function(g) { return g.id.startsWith(CONFERENCE_ID + '/Paper' + num + '/Area_Chair_'); });
        if (anonGroup) {
          anonids[num] = anonGroup.id;
          areaChairPaperNums.push(parseInt(num));
        }
      } else {
        primaryAreaChairs[num] = areaChairGroup.members.filter(function(m) { return m.startsWith('~'); });
      }
    });
    return {
      areaChairPaperNums: areaChairPaperNums,
      secondaryAreaChairPaperNums: secondaryAreaChairPaperNums,
      secondaryAreaChairPrimaryACs: primaryAreaChairs
    };
  });

  return $.when(allAreaChairGroupsP);
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
    return paper.replace(name, '');
  } else {
    return null;
  }
};

var getPaperNumbersfromGroups = function(groups) {
  return _.uniq(_.map(groups, function(group) {
    return parseInt(getNumberfromGroup(group.id, 'Paper'));
  }));
};

var buildNoteMap = function(noteNumbers) {
  var noteMap = Object.create(null);
  for (var i = 0; i < noteNumbers.length; i++) {
    noteMap[noteNumbers[i]] = Object.create(null);
  }
  return noteMap;
};

var getInvitationId = function(name, number) {
  return CONFERENCE_ID + '/Paper' + number + '/-/' + name;
};

var getInvitationRegex = function(name, numberStr) {
  return '^' + CONFERENCE_ID + '/Paper(' + numberStr + ')/-/' + name;
};

// Ajax functions
var loadData = function(paperNums) {
  var acPapers = paperNums.areaChairPaperNums;
  var secondaryAcPapers = paperNums.secondaryAreaChairPaperNums;
  var secondaryAreaChairPrimaryACs = paperNums.secondaryAreaChairPrimaryACs;
  var noteNumbers = _.uniq(_.concat(acPapers, secondaryAcPapers));
  var blindedNotesP;
  var allReviewersP;
  var assignedSACsP = $.Deferred().resolve([]);

  if (noteNumbers.length) {
    var noteNumbersStr = noteNumbers.join(',');

    blindedNotesP = Webfield.getAll('/notes', {
      invitation: BLIND_SUBMISSION_ID,
      number: noteNumbersStr,
      select: 'id,number,forum,content,details,invitation',
      details: 'invitation,replyCount,directReplies',
      sort: 'number:asc'
    }).then(function(notes) {
      return _.sortBy(notes, 'number');
    });

  } else {
    blindedNotesP = $.Deferred().resolve([]);
  }

  if (ENABLE_REVIEWER_REASSIGNMENT) {
    allReviewersP = Webfield.get('/groups', { id: REVIEWER_GROUP, select: 'members' })
    .then(function(result) {
      return result.groups[0].members;
    });
  } else {
    allReviewersP = $.Deferred().resolve([]);
  }

  var acPaperRankingsP = Webfield.get('/tags', { invitation: PAPER_RANKING_ID })
  .then(function (result) {
    return _.keyBy(result.tags, 'forum');
  });

  var reviewerPaperRankingsP = Webfield.get('/tags', { invitation: REVIEWER_PAPER_RANKING_ID })
  .then(function (result) {
    return result.tags.reduce(function(rankingByForum, tag) {
      if (!rankingByForum[tag.forum]) {
        rankingByForum[tag.forum] = {};
      }
      var index = getNumberfromGroup(tag.signatures[0], 'Reviewer_');
      rankingByForum[tag.forum][index] = tag;
      return rankingByForum;
    }, {});
  });

  if (SENIOR_AREA_CHAIRS_ID) {
    assignedSACsP = Webfield.get('/edges', { invitation: SENIOR_AREA_CHAIRS_ID + '/-/Assignment', head: user.profile.id })
    .then(function(result) {
      if (result && result.edges.length) {
        return result.edges.map(function (edge) {
          return edge.tail;
        });
      }
      return []
    })

  }

  return $.when(
    blindedNotesP,
    getReviewerGroups(noteNumbers),
    getAllInvitations(),
    allReviewersP,
    acPaperRankingsP,
    reviewerPaperRankingsP,
    acPapers,
    secondaryAcPapers,
    secondaryAreaChairPrimaryACs,
    assignedSACsP
  );
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

var getReviewerGroups = function(noteNumbers) {
  if (!noteNumbers.length) {
    return $.Deferred().resolve({});
  }

  var noteMap = buildNoteMap(noteNumbers);

  return Webfield.getAll('/groups', {
    regex: CONFERENCE_ID + '/Paper.*',
    select: 'id,members'
  })
  .then(function(groups) {
    var anonGroups = _.filter(groups, function(g) { return g.id.includes('/Reviewer_'); });
    var reviewerGroups = _.filter(groups, function(g) { return g.id.endsWith('/Reviewers'); });

    _.forEach(reviewerGroups, function(g) {
      var num = getNumberfromGroup(g.id, 'Paper');
      if (num in noteMap) {
          g.members.forEach(function(member, index) {
            var anonGroup = anonGroups.find(function(g) { return g.id.startsWith(CONFERENCE_ID + '/Paper' + num + '/Reviewer_') && g.members[0] == member; });
            if (anonGroup) {
              var anonId = getNumberfromGroup(anonGroup.id, 'Reviewer_')
              noteMap[num][anonId] = member;
            }
          });
      }
    });

    return noteMap;
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
    return _.some(inv.invitees, function(invitee) { return invitee.indexOf(AREA_CHAIR_NAME) !== -1 || (SECONDARY_AREA_CHAIR_NAME && invitee.indexOf(SECONDARY_AREA_CHAIR_NAME) !== -1); });
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

var formatData = function(blindedNotes, noteToReviewerIds, invitations, allReviewers, acRankingByPaper, reviewerRankingByPaper, acPapers, secondaryAcPapers, secondaryAreaChairPrimaryACs, assignedSACs) {

  var uniqueIds = _.uniq(_.concat(_.reduce(noteToReviewerIds, function(result, idsObj, noteNum) {
    return result.concat(_.values(idsObj));
  }, []), allReviewers));

  if (assignedSACs.length) {
    uniqueIds.concat(assignedSACs);
  }

  return getUserProfiles(uniqueIds)
  .then(function(profiles) {

    reviewerOptions = _.map(allReviewers, function(r) {
      var profile = findProfile(profiles, r);
      return {
        id: profile.id,
        description: view.prettyId(profile.name) + ' (' + profile.allEmails.join(', ') + ')'
      }
    });

    conferenceStatusData = {
      profiles: profiles,
      blindedNotes: blindedNotes,
      noteToReviewerIds: noteToReviewerIds,
      invitations: invitations,
      acRankingByPaper: acRankingByPaper,
      reviewerRankingByPaper: reviewerRankingByPaper,
      acPapers: acPapers,
      secondaryAcPapers: secondaryAcPapers,
      secondaryAreaChairPrimaryACs: secondaryAreaChairPrimaryACs,
      sacProfiles: assignedSACs.length ? assignedSACs.map(function (assignedSAC) {
        return findProfile(profiles, assignedSAC);
      }) : []
    };
    return conferenceStatusData;
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

// Render functions
var renderHeader = function() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);

  if (ENABLE_EDIT_REVIEWER_ASSIGNMENTS) {
    HEADER.instructions += '<p><strong>Reviewer Assignment Browser: </strong><a id="edge_browser_url" href="' + EDGE_BROWSER_URL + '" target="_blank" rel="nofollow">Modify Reviewer Assignments</a></p>';
  }

  Webfield.ui.header(HEADER.title, HEADER.instructions);

  var loadingMessage = '<p class="empty-message">Loading...</p>';
  var tabsList = [
    {
      heading: 'Assigned Papers',
      id: 'assigned-papers',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll',
      active: true
    }
    // {
    //   heading: 'Area Chair Schedule',
    //   id: 'areachair-schedule',
    //   content: HEADER.schedule
    // },
  ];

  if (SECONDARY_AREA_CHAIR_NAME) {
    tabsList.push(
      {
        heading: 'Secondary AC Assignments',
        id: 'secondary-papers',
        content: loadingMessage
      }
    );
  }

  tabsList.push(
    {
      heading: 'Area Chair Tasks',
      id: 'areachair-tasks',
      content: loadingMessage
    }
  );

  Webfield.ui.tabPanel(tabsList);
};

var renderTable = function(rows, container, secondary_meta) {
  renderTableRows(rows, container, secondary_meta);
  if (showRankings && !secondary_meta) {
    postRenderTable(rows.map(function (row) {
      return Object.values(row);
    }));
  }
}

var renderStatusTable = function(conferenceStatusData, container) {
  var assignedNotes = _.filter(conferenceStatusData.blindedNotes, function(note) { return conferenceStatusData.acPapers.indexOf(note.number) > -1; });
  var rows = _.map(assignedNotes, function(note) {
    var reviewersById = conferenceStatusData.noteToReviewerIds[note.number] || Object.create(null);

    var metaReview = _.find(note.details.directReplies, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, note.number)]);
    var noteCompletedReviews = getOfficialReviews((note.details.directReplies || []).filter(function(reply) { return reply.invitation === getInvitationId(OFFICIAL_REVIEW_NAME, note.number); }));
    var metaReviewInvitation = _.find(conferenceStatusData.invitations, ['id', getInvitationId(OFFICIAL_META_REVIEW_NAME, note.number)]);

    return buildTableRow(note, reviewersById, noteCompletedReviews, metaReview, metaReviewInvitation, conferenceStatusData.acRankingByPaper[note.forum], conferenceStatusData.reviewerRankingByPaper[note.forum] || {});
  });

  var filteredRows = null;
  var toNumber = function(value) {
    return value === 'N/A' ? 0 : value;
  }

  // Sort form handler
  var order = 'desc';

  var sortOptions = {
    Paper_Number: function(row) { return row.paperNumber.number; },
    Paper_Title: function(row) { return _.toLower(_.trim(row.note.content.title)); },
    Number_of_Forum_Replies: function(row) { return row.reviewProgressData.forumReplyCount; },
    Number_of_Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
    Number_of_Reviews_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedReviews; },
    Average_Rating: function(row) { return toNumber(row.reviewProgressData.averageRating); },
    Max_Rating: function(row) { return toNumber(row.reviewProgressData.maxRating); },
    Min_Rating: function(row) { return toNumber(row.reviewProgressData.minRating); },
    Rating_Range: function(row) { return toNumber(row.reviewProgressData.maxRating) - toNumber(row.reviewProgressData.minRating); },
    Average_Confidence: function(row) { return toNumber(row.reviewProgressData.averageConfidence); },
    Max_Confidence: function(row) { return toNumber(row.reviewProgressData.maxConfidence); },
    Min_Confidence: function(row) { return toNumber(row.reviewProgressData.minConfidence); },
    Confidence_Range: function(row) { return toNumber(row.reviewProgressData.maxConfidence) - toNumber(row.reviewProgressData.minConfidence); },
    Meta_Review_Recommendation: function(row) { return row.metaReviewData.recommendation; }
  };

  if (showRankings) {
    sortOptions.Paper_Ranking = function(row) { return parseInt(row[4].ranking && row[4].ranking.tag); }
  }

  var sortResults = function(newOption, switchOrder) {
    if (switchOrder) {
      order = order === 'asc' ? 'desc' : 'asc';
    }
    renderTable(_.orderBy(filteredRows === null ? rows : filteredRows, sortOptions[newOption], order), container);
  }

  var searchResults = function(searchText,isQueryMode) {
    $(container + ' #form-sort').val('Paper_Number');

    // Currently only searching on note number and note title
    var filterFunc = function(row) {
      return (
        (row.note.number + '').indexOf(searchText) === 0 ||
        row.note.content.title.toLowerCase().indexOf(searchText) !== -1
      );
    };

    if (searchText) {
      if (isQueryMode) {
        var filterResult = Webfield.filterCollections(rows, searchText.slice(1), filterOperators, propertiesAllowed, 'note.id')
        filteredRows = filterResult.filteredRows;
        queryIsInvalid = filterResult.queryIsInvalid;
        if(queryIsInvalid) $(container + ' .form-search').addClass('invalid-value')
      } else {
        filteredRows = _.filter(rows, filterFunc)
      }
      filteredRows = _.orderBy(filteredRows, sortOptions['Paper_Number'], 'asc');
      order = 'asc'
    } else {
      filteredRows = rows;
    }
    if (rows.length !== filteredRows.length) {
      conferenceStatusData.filteredNotes = filteredRows.map(function (p) {
        return p.note;
      });
    }
    renderTable(filteredRows, container);
  };

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
      return _.includes(selectedIds, row.note.forum);
    });

    selectedRows.forEach(function(row) {
      var users = _.values(row.reviewProgressData.reviewers);
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

  //#region sortBarHtml
  var sortBarHtml = '<form class="form-inline search-form clearfix" role="search">' +
    '<div id="div-msg-reviewers" class="btn-group" role="group">' +
      '<button id="message-reviewers-btn" type="button" class="btn btn-icon dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" title="Select papers to message corresponding reviewers" disabled="disabled">' +
        '<span class="glyphicon glyphicon-envelope"></span> &nbsp;Message ' +
        '<span class="caret"></span>' +
      '</button>' +
      '<ul class="dropdown-menu" aria-labelledby="grp-msg-reviewers-btn">' +
        '<li><a id="msg-all-reviewers">All Reviewers of selected papers</a></li>' +
        '<li><a id="msg-submitted-reviewers">Reviewers of selected papers with submitted reviews</a></li>' +
        '<li><a id="msg-unsubmitted-reviewers">Reviewers of selected papers with unsubmitted reviews</a></li>' +
      '</ul>' +
    '</div>' +
    '<div class="btn-group"><button class="btn btn-export-data" type="button">Export</button></div>' +
    '<div class="btn-group"><button class="btn btn-export-pdf" type="button">Download PDF</button></div>' +
    '<div class="pull-right">' +
      '<strong style="vertical-align: middle;">Search:</strong>' +
      '<input type="text" class="form-search form-control" class="form-control" placeholder="Enter search term or type + to start a query and press enter" style="width:380px; margin-right: 0.5rem; line-height: 34px;">' +
      '<strong>Sort By:</strong> ' +
      '<select id="form-sort" class="form-control" style="width: 200px; line-height: 1rem;">' + sortOptionHtml + '</select>' +
      '<button id="form-order" class="btn btn-icon" type="button"><span class="glyphicon glyphicon-sort"></span></button>' +
    '</div>' +
  '</form>';
  //#endregion

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

  $(container + ' .form-search').on('keyup', function (e) {
    var searchText = $(container + ' .form-search').val().trim();
    var searchLabel = $(container + ' .form-search').prevAll('strong:first').text();
    conferenceStatusData.filteredNotes = null
    $(container + ' .form-search').removeClass('invalid-value');

    if (searchText.startsWith('+')) {
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
      if (searchLabel !== 'Search:') {
        $(container + ' .form-search').prev().remove(); // remove info icon

        $(container + ' .form-search').prev().text('Search:');
      }

      _.debounce(function () {
        searchResults(searchText.toLowerCase(),false);
      }, 300)();
    }
  });

  $(container + ' form.search-form').on('submit', function() {
    return false;
  });

  if (rows.length) {
    renderTable(rows, container);
  } else {
    $(container).empty().append('<p class="empty-message">No assigned papers. ' +
    'Check back later or contact info@openreview.net if you believe this to be an error.</p>');
  }
};

var renderSecondaryStatusTable = function(conferenceStatusData, container) {
  var assignedNotes = _.filter(conferenceStatusData.blindedNotes, function(note) { return conferenceStatusData.secondaryAcPapers.indexOf(note.number) > -1; })
  var rows = _.map(assignedNotes, function(note) {
    var revIds = conferenceStatusData.noteToReviewerIds[note.number] || Object.create(null);
    var metaReview = _.find(note.details.directReplies, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, note.number)]);
    var noteCompletedReviews = getOfficialReviews((note.details.directReplies || []).filter(function(reply) { return reply.invitation === getInvitationId(OFFICIAL_REVIEW_NAME, note.number); }));


    return buildTableRow(note, revIds, noteCompletedReviews, metaReview, undefined, conferenceStatusData.acRankingByPaper[note.forum], conferenceStatusData.reviewerRankingByPaper[note.forum] || {}, 'secondary', conferenceStatusData.secondaryAreaChairPrimaryACs);
  });

  rows = Object.values(rows)

  var order = 'desc';

  var sortOptions = {
    Paper_Number: function(row) { return row.paperNumber.number; },
    Paper_Title: function(row) { return _.toLower(_.trim(row.note.content.title)); },
    Number_of_Forum_Replies: function(row) { return row.reviewProgressData.forumReplyCount; },
    Number_of_Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
    Number_of_Reviews_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedReviews; },
    Average_Rating: function(row) { return row.reviewProgressData.averageRating === 'N/A' ? 0 : row.reviewProgressData.averageRating; },
    Max_Rating: function(row) { return row.reviewProgressData.maxRating === 'N/A' ? 0 : row.reviewProgressData.maxRating; },
    Min_Rating: function(row) { return row.reviewProgressData.minRating === 'N/A' ? 0 : row.reviewProgressData.minRating; },
    Average_Confidence: function(row) { return row.reviewProgressData.averageConfidence === 'N/A' ? 0 : row.reviewProgressData.averageConfidence; },
    Max_Confidence: function(row) { return row.reviewProgressData.maxConfidence === 'N/A' ? 0 : row.reviewProgressData.maxConfidence; },
    Min_Confidence: function(row) { return row.reviewProgressData.minConfidence === 'N/A' ? 0 : row.reviewProgressData.minConfidence; },
    Meta_Review_Recommendation: function(row) { return row.metaReviewData.recommendation; }
  };

  var sortResults = function(newOption, switchOrder) {
    if (switchOrder) {
      order = order === 'asc' ? 'desc' : 'asc';
    }
    renderTable(_.orderBy(rows, sortOptions[newOption], order), container, true);
  }

  var sortOptionHtml = Object.keys(sortOptions).map(function(option) {
    return '<option value="' + option + '">' + option.replace(/_/g, ' ') + '</option>';
  }).join('\n');

  var sortBarHtml = '<form class="form-inline search-form clearfix" role="search">' +
    '<div class="pull-right">' +
      '<strong>Sort By:</strong> ' +
      '<select id="form-sort-secondary" class="form-control">' + sortOptionHtml + '</select>' +
      '<button id="form-order-secondary" class="btn btn-icon"><span class="glyphicon glyphicon-sort"></span></button>' +
    '</div>' +
  '</form>';
  if (rows.length) {
    $(container).empty().append(sortBarHtml);
  }

  // Need to add event handlers for these controls inside this function so they have access to row
  // data
  $('#form-sort-secondary').on('change', function(e) {
    sortResults($(e.target).val(), false);
  });
  $('#form-order-secondary').on('click', function(e) {
    sortResults($(this).prev().val(), true);
    return false;
  });

  if (rows.length) {
    renderTable(rows, container, true);
  } else {
    $(container).empty().append('<p class="empty-message">No assigned papers. ' +
    'Check back later or contact info@openreview.net if you believe this to be an error.</p>');
  }
};

var updateReviewerContainer = function (paperNumber, renderEmptyDropdown) {
  renderEmptyDropdown = renderEmptyDropdown || false;
  $addReviewerContainer = $('#' + paperNumber + '-add-reviewer');
  $reviewerProgressContainer = $('#' + paperNumber + '-reviewer-progress');
  paperForum = $reviewerProgressContainer.data('paperForum');

  var paperNoteId = reviewerSummaryMap[paperNumber].noteId;
  var dropdownOptions = [];
  if (!renderEmptyDropdown) {
    var reviewersToRender = reviewerOptions;
    var reviewerWithConflictForThisPaper = paperAndReviewersWithConflict[paperNumber];
    if (reviewerWithConflictForThisPaper) {
      reviewersToRender = reviewerOptions.filter(function (reviewerOption) {
        return reviewerWithConflictForThisPaper.indexOf(reviewerOption.id) === -1;
      })
    };
    dropdownOptions = reviewersToRender;
  }

  var filterOptions = function(options, term) {
    return _.filter(options, function(p) {
      return _.includes(p.description.toLowerCase(), term.toLowerCase());
    });
  };
  placeholder = 'reviewer@domain.edu';

  var $dropdown = view.mkDropdown(placeholder, false, null, function(update, term) {
    update(filterOptions(dropdownOptions, term));
  }, function(value, id) {
    var selectedOption = _.find(dropdownOptions, ['id', id]);
    var $input = $dropdown.find('input');

    if (!(selectedOption && selectedOption.description === value)) {
      $input.val(value);
      $input.attr('value_id', value);
    } else {
      $input.val(value);
      $input.attr('value_id', id);
    }
  });

  $dropdown.find('input').attr({
    class: 'form-control dropdown note_content_value input-assign-reviewer',
    name: placeholder,
    autocomplete: 'on'
  });
  $dropdown.find('div').attr({
    class: 'dropdown_content dropdown_content_assign_reviewer',
    name: placeholder,
    autocomplete: 'on'
  });

  $addReviewerContainer.append($dropdown);
  $addReviewerContainer.append('<button class="btn btn-xs btn-assign-reviewer" data-paper-number=' + paperNumber + ' data-paper-forum=' + paperForum +'>Assign</button>');
}

var renderTableRows = function(rows, container, secondary_meta) {
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
    secondary_meta ? Handlebars.templates.noteAreaChairs : Handlebars.templates.noteMetaReviewStatus
  ];
  var rowsHtml = rows.map(function(row) {
    return Object.values(row).map(function(cell, i) {
      return templateFuncs[i](cell);
    });
  });

  var tableHtml = Handlebars.templates['components/table']({
    headings: [
      '<input type="checkbox" id="select-all-papers">', '#', 'Paper Summary',
      'Review Progress', 'Meta Review Status'
    ],
    rows: rowsHtml,
    extraClasses: 'ac-console-table'
  });

  $('.table-container', container).remove();
  $(container).append(tableHtml);
}

var postRenderTable = function(rows) {
  if (paperRankingInvitation) {
    currentRankings = [];
    rows.forEach(function(row) {
      if (row[4].ranking && row[4].ranking.tag !== 'No Ranking') {
        currentRankings.push(row[4].ranking.tag);
      }
    });
    paperRankingInvitation.reply.content.tag['value-dropdown'] = _.difference(availableOptions, currentRankings);
  }
  var invitationId = paperRankingInvitation ? paperRankingInvitation.id : PAPER_RANKING_ID;

  rows.forEach(function(row) {
    var noteId = row[4].noteId;
    var noteNumber = row[4].paperNumber;
    var paperRanking = row[4].ranking;
    $metaReviewStatusContainer = $('#' + noteNumber + '-metareview-status');
    if (!$metaReviewStatusContainer.length) {
      return;
    }

    var $tagWidget = view.mkTagInput(
      'tag',
      paperRankingInvitation && paperRankingInvitation.reply.content.tag,
      paperRanking ? [paperRanking] : [],
      {
        forum: noteId,
        placeholder: (paperRankingInvitation && paperRankingInvitation.reply.content.tag.description) || view.prettyInvitationId(invitationId),
        label: view.prettyInvitationId(invitationId),
        readOnly: false,
        onChange: function(id, value, deleted, done) {
          var body = {
            id: id,
            tag: value,
            signatures: [anonids[noteNumber]],
            readers: [anonids[noteNumber]],
            forum: noteId,
            invitation: invitationId,
            ddate: deleted ? Date.now() : null
          };
          body = view.getCopiedValues(body, paperRankingInvitation.reply);
          $('.tag-widget button').attr('disabled', true);
          Webfield.post('/tags', body)
          .then(function(result) {
            row[4].ranking = result; //not sure if this is the best way to do it
            postRenderTable(rows);
            done(result);
          })
          .fail(function(error) {
            promptError(error ? error : 'The specified tag could not be updated');
          });
        }
      }
    );
    $metaReviewStatusContainer.find('.tag-widget').remove();
    $metaReviewStatusContainer.append($tagWidget);
  });
};

var renderTasks = function(invitations) {
  //  My Tasks tab
  var tasksOptions = {
    container: '#areachair-tasks',
    emptyMessage: 'No outstanding tasks for this conference',
    referrer: encodeURIComponent('[Area Chair Console](/group?id=' + CONFERENCE_ID + '/' + AREA_CHAIR_NAME + '#areachair-tasks)')
  }
  $(tasksOptions.container).empty();

  Webfield.ui.newTaskList(invitations, [], tasksOptions);
  $('.tabs-container a[href="#areachair-tasks"]').parent().show();
}

var renderTableAndTasks = function(fetchedData) {
  var sacProfiles = fetchedData.sacProfiles.filter(function (profile) {
    return profile.id;
  })
  if (sacProfiles.length>1) {
    var sacProfileLinks = sacProfiles.map(function (profile) {
      return '<a href="https://openreview.net/profile?id=' + profile.id + '" target="_blank">' + view.prettyId(profile.id) + ' </a> (' + profile.email + ')';
    });
    $('#header .description').append(
      '<p class="dark">Your assigned Senior Area Chair are '+ sacProfileLinks.join(' , ') +'.</p>'
    );
  } else if(sacProfiles.length){
    $('#header .description').append(
      '<p class="dark">Your assigned Senior Area Chair is <a href="https://openreview.net/profile?id=' + sacProfiles[0].id + '" target="_blank">' + view.prettyId(sacProfiles[0].id) + ' </a> (' + sacProfiles[0].email + ').</p>'
    );
  }


  renderTasks(fetchedData.invitations);

  paperRankingInvitation = _.find(fetchedData.invitations, ['id', PAPER_RANKING_ID]);
  var primaryAssignments = _.filter(fetchedData.blindedNotes, function(note) { return fetchedData.acPapers.indexOf(note.number) > -1; });
  if (paperRankingInvitation) {
    availableOptions = ['No Ranking'];

    primaryAssignments.forEach(function(note, index) {
      availableOptions.push((index + 1) + ' of ' + primaryAssignments.length );
    })
  }
  if (paperRankingInvitation || Object.keys(fetchedData.acRankingByPaper).length) {
    showRankings = true;
  }

  renderStatusTable(
    fetchedData,
    '#assigned-papers'
  );

  if (SECONDARY_AREA_CHAIR_NAME) {
    renderSecondaryStatusTable(
      fetchedData,
      '#secondary-papers'
    );
  }

  registerEventHandlers();

  Webfield.ui.done();
}

var buildTableRow = function(note, reviewerIds, completedReviews, metaReview, metaReviewInvitation, acPaperRanking, reviewerPaperRanking, typeMetaReviewer, secondaryAreaChairPrimaryACs) {
  var cellCheck = { selected: false, noteId: note.id };
  var referrerContainer = typeMetaReviewer === 'secondary' ? '#secondary-papers' : '#assigned-papers' ;
  var referrerUrl = encodeURIComponent('[Area Chair Console](/group?id=' + CONFERENCE_ID + '/' + AREA_CHAIR_NAME + referrerContainer + ')');

  // Paper number cell
  var cell0 = {
    number: note.number
  };

  // Note summary cell
  note.content.authors = null;  // Don't display 'Blinded Authors'
  var cell1 = note;
  cell1.referrer = referrerUrl;

  // Review progress cell
  var reviewObj;
  var combinedObj = {};
  var ratings = [];
  var confidences = [];
  for (var reviewerNum in reviewerIds) {
    var reviewerId = reviewerIds[reviewerNum];
    var reviewer = findProfile(conferenceStatusData.profiles, reviewerId);
    if (reviewerNum in completedReviews) {
      reviewObj = completedReviews[reviewerNum];
      paperRanking = reviewerPaperRanking[reviewerNum];
      combinedObj[reviewerNum] = {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
        completedReview: true,
        forum: reviewObj.forum,
        note: reviewObj.id,
        rating: reviewObj.rating,
        confidence: reviewObj.confidence,
        reviewLength: reviewObj.content.review && reviewObj.content.review.length,
        ranking: paperRanking && paperRanking.tag
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
        forum: note.forum,
        forumUrl: forumUrl,
        lastReminderSent: lastReminderSent ? new Date(parseInt(lastReminderSent)).toLocaleDateString() : lastReminderSent,
        paperNumber: note.number,
        reviewerNumber: reviewerNum
      };
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

  var cell2 = {
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
    enableReviewerReassignment : ENABLE_REVIEWER_REASSIGNMENT,
    referrer: referrerUrl
  };
  reviewerSummaryMap[note.number] = cell2;

  // Status cell
  var invitationUrlParams = {
    id: note.forum,
    noteId: note.id,
    invitationId: getInvitationId('Meta_Review', note.number),
    referrer: referrerUrl
  };
  var cell3 = {
    noteId: note.id,
    paperNumber: note.number,
    ranking: acPaperRanking
  };
  if (metaReview) {
    // if the field is not present the space will still cause the link to be displayed
    cell3.recommendation = metaReview.content[META_REVIEW_CONTENT_FIELD] || ' ';
    cell3.editUrl = '/forum?id=' + note.forum + '&noteId=' + metaReview.id + '&referrer=' + referrerUrl;
  }
  if (metaReviewInvitation) {
    cell3.invitationUrl = '/forum?' + $.param(invitationUrlParams);;
  }

  if (typeMetaReviewer == 'secondary') {
    cell3 = {
      numMetaReview: metaReview ? 'One' : 'No',
      areachair: { name: secondaryAreaChairPrimaryACs[note.number].map(function(m) { return view.prettyId(m);}) },
      metaReview: metaReview,
      referrer: referrerUrl
    }
  }

  return {
    cellCheck: cellCheck,
    paperNumber: cell0,
    note: cell1,
    reviewProgressData: cell2,
    metaReviewData: cell3,
  }
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

  $('#group-container').on('click', 'a.collapse-btn', function(e) {
    var paperIdArray = $(this).attr('href').split("-");//href attribute is in format of #{paperId}-reviewers
    paperIdArray.pop(); //
    var paperId = paperIdArray.join('-').substring(1);
    var paperIndex = Object.keys(reviewerSummaryMap).filter(function (p) {
      return reviewerSummaryMap[p].noteId === paperId;
    })
    var paperNumber = reviewerSummaryMap[paperIndex].paperNumber;
    if ($(this).text() === 'Show reviewers') {
      $(this).text('Hide reviewers');
      updateReviewerContainer(paperNumber, true);//render empty dropdown as placeholder for visual consistency
      Webfield.get('/edges', {
        head: paperId,
        invitation: REVIEWER_GROUP_WITH_CONFLICT
      }).then(function (result) {
        var reviewerWithConflictForThisPaper = result.edges.map(function (p) {
          return p.tail;
        });
        paperAndReviewersWithConflict[paperNumber]=reviewerWithConflictForThisPaper;
        $addReviewerContainer.children().remove(); //remove empty dropdown when actual data arrive
        updateReviewerContainer(paperNumber, false); //render dropdown with filtered value
      });
    } else {
      $(this).text('Show reviewers');
      $(paperNumber + '-add-reviewer').children().remove()
    }
  });

  $('#group-container').on('click', 'button.btn.btn-assign-reviewer', function(e) {
    var $link = $(this);
    var paperNumber = $link.data('paperNumber');
    var paperForum = $link.data('paperForum');
    var $currDiv = $('#' + paperNumber + '-add-reviewer');
    var userToAdd = $currDiv.find('input').attr('value_id').trim();

    if (!userToAdd || !((userToAdd.indexOf('@') > 0) || _.startsWith(userToAdd, '~'))) {
      // this checks if no input was given, OR  if the given input neither has an '@' nor does it start with a '~'
      promptError('Please enter a valid email for assigning a reviewer');
      return false;
    }
    var alreadyAssigned = _.find(reviewerSummaryMap[paperNumber].reviewers, function(rev){
      return (rev.email === userToAdd) || (rev.id === userToAdd);
    });
    if (alreadyAssigned) {
      promptError('Reviewer ' + view.prettyId(userToAdd) + ' has already been assigned to Paper ' + paperNumber.toString());
      return false;
    }

    var reviewersWithConflict = paperAndReviewersWithConflict[paperNumber];

    //if input is a reviewer in conflict, show error no matter of ENABLE_REVIEWER_REASSIGNMENT_TO_OUTSIDE_REVIEWERS flag
    if(reviewersWithConflict && _.includes(reviewersWithConflict, userToAdd)){
      promptError('The reviewer entered is invalid');
      $currDiv.find('input').val('');
      $currDiv.find('input').attr('value_id', '');
      return false;
    }

    if (!ENABLE_REVIEWER_REASSIGNMENT_TO_OUTSIDE_REVIEWERS) { //check only if reassign to outside is disabled
      var insideReviewer = reviewerOptions.find(function (reviewerOption) {
        return reviewerOption.id === userToAdd;
      })
      if (!insideReviewer) { // not in allreviewers means is a outside reviewer
        promptError('Please choose only reviewers from the dropdown');
        $currDiv.find('input').val('');
        $currDiv.find('input').attr('value_id', '');
        return false;
      }
    }

    if (!_.startsWith(userToAdd, '~')) {
      userToAdd = userToAdd.toLowerCase();
    }

    var reviewerProfile = {
      'email' : userToAdd,
      'id' : userToAdd,
      'name': '',
      'content': {'names': [{'username': userToAdd}]}
    };

    getUserProfiles([userToAdd])
    .then(function (userProfile){
      if (userProfile && Object.keys(userProfile).length){
        reviewerProfile = userProfile[Object.keys(userProfile)[0]];
      }
      return Webfield.put('/groups/members', {
        id: CONFERENCE_ID + '/Paper' + paperNumber + '/Reviewers',
        members: [reviewerProfile.id]
      })
    })
    .then(function(result) {
      return Webfield.put('/groups/members', {
        id: REVIEWER_GROUP,
        members: [reviewerProfile.id]
      })
    })
    .then(function(result) {
      return Webfield.get('/groups', {
        id: CONFERENCE_ID + '/Paper' + paperNumber + '/Reviewer_.*',
        member: reviewerProfile.id
      })
    })
    .then(function(result) {
      var nextAnonNumber = getNumberfromGroup(result.groups[0].id, 'Reviewer_');
      var forumUrl = 'https://openreview.net/forum?' + $.param({
        id: paperForum,
        invitationId: CONFERENCE_ID + '/-/Paper' + paperNumber + '/Official_Review'
      });
      var lastReminderSent = null;
      reviewerSummaryMap[paperNumber].reviewers[nextAnonNumber] = {
        id: reviewerProfile.id,
        name: reviewerProfile.name,
        email: reviewerProfile.email,
        forum: paperForum,
        forumUrl: forumUrl,
        lastReminderSent: lastReminderSent,
        paperNumber: paperNumber,
        reviewerNumber: nextAnonNumber
      };
      reviewerSummaryMap[paperNumber].numReviewers = reviewerSummaryMap[paperNumber].numReviewers ? reviewerSummaryMap[paperNumber].numReviewers + 1 : 1;
      reviewerSummaryMap[paperNumber].expandReviewerList = true;
      reviewerSummaryMap[paperNumber].sendReminder = true;
      reviewerSummaryMap[paperNumber].showActivityModal = true;
      reviewerSummaryMap[paperNumber].enableReviewerReassignment = ENABLE_REVIEWER_REASSIGNMENT;
      var $revProgressDiv = $('#' + paperNumber + '-reviewer-progress');
      $revProgressDiv.html(Handlebars.templates.noteReviewers(reviewerSummaryMap[paperNumber]));
      updateReviewerContainer(paperNumber);
      promptMessage('Email has been sent to ' + view.prettyId(reviewerProfile.id) + ' about their new assignment to paper ' + paperNumber, { overlay: true });
      var postData = {
        groups: [reviewerProfile.id],
        subject: SHORT_PHRASE + ": You have been assigned as a Reviewer for paper number " + paperNumber,
        message: 'This is to inform you that you have been assigned as a Reviewer for paper number ' + paperNumber +
        ' for ' + SHORT_PHRASE + '.' +
        '\n\nTo review this new assignment, please login to OpenReview and go to ' +
        'https://openreview.net/forum?id=' + paperForum + '&invitationId=' + getInvitationId(OFFICIAL_REVIEW_NAME, paperNumber.toString()) +
        '\n\nTo check all of your assigned papers, go to https://openreview.net/group?id=' + REVIEWER_GROUP +
        '\n\nThank you,\n' + SHORT_PHRASE + ' Area Chair'
      };
      return Webfield.post('/messages', postData);
    });
    return false;
  });

  $('#group-container').on('click', 'a.unassign-reviewer-link', function(e) {
    var $link = $(this);
    var userId = $link.data('userId');
    var paperNumber = $link.data('paperNumber');
    var reviewerNumber = $link.data('reviewerNumber');

    Webfield.delete('/groups/members', {
      id: CONFERENCE_ID + '/Paper' + paperNumber + '/Reviewers',
      members: [reviewerSummaryMap[paperNumber].reviewers[reviewerNumber].id, reviewerSummaryMap[paperNumber].reviewers[reviewerNumber].email]
    })
    .then(function(result) {
      var $revProgressDiv = $('#' + paperNumber + '-reviewer-progress');
      delete reviewerSummaryMap[paperNumber].reviewers[reviewerNumber];
      reviewerSummaryMap[paperNumber].numReviewers = reviewerSummaryMap[paperNumber].numReviewers ? reviewerSummaryMap[paperNumber].numReviewers - 1 : 0;
      reviewerSummaryMap[paperNumber].expandReviewerList = true;
      $revProgressDiv.html(Handlebars.templates.noteReviewers(reviewerSummaryMap[paperNumber]));
      updateReviewerContainer(paperNumber);
      promptMessage('Reviewer ' + view.prettyId(userId) + ' has been unassigned for paper ' + paperNumber, { overlay: true });
    })
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
    var notes = conferenceStatusData.filteredNotes ? conferenceStatusData.filteredNotes : conferenceStatusData.blindedNotes;
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
      var metaReview = _.find(note.details.directReplies, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, note.number)]);
      var noteCompletedReviews = getOfficialReviews((note.details.directReplies || []).filter(function(reply) { return reply.invitation === getInvitationId(OFFICIAL_REVIEW_NAME, note.number); }));
      var paperTableRow = Object.values(buildTableRow(note, revIds, noteCompletedReviews, metaReview, null, acRankingByPaper[note.forum], reviewerRankingByPaper[note.forum] || {}));

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
      metaReview && metaReview.content[META_REVIEW_CONTENT_FIELD]
      ].join(',') + '\n');
    });
    return [rowData.join('')];
  };

  $('#group-container').on('click', 'button.btn.btn-export-data', function(e) {
    var blob = new Blob(buildCSV(), {type: 'text/csv'});
    saveAs(blob, SHORT_PHRASE.replace(/\s/g, '_').concat(conferenceStatusData.filteredNotes ? '_AC_paper_status(Filtered).csv' : '_AC_paper_status.csv'));
    return false;
  });

  $("#group-container").on("click", "button.btn.btn-export-pdf", function (e) {
    const ids = _.flatMap(conferenceStatusData.blindedNotes, function (note) {
        return note.content.pdf ? note.id : [];
      })
    if(!ids.length) {
        promptError('No submission contains PDF');
        return
    }
    $("button.btn.btn-export-pdf")
      .prop("disabled", true)
      .html(
        "<div class='spinner-small'><div class='rect1'></div><div class='rect2'></div><div class='rect3'></div><div class='rect4'></div><div class='rect5'></div></div>"
      );
    Webfield.get("/attachment", {
      ids,
      name: "pdf"
    }, {
      isBlob: true,
      handleErrors: false
    }).then(function (result) {
      saveAs(result, SHORT_PHRASE.replace(/\s/g, "_") + "_pdfs.zip");
      $("button.btn.btn-export-pdf").prop("disabled", false).html("Download PDF");
    }, function () {
      promptError('PDF download failed');
      $("button.btn.btn-export-pdf").prop("disabled", false).html("Download PDF");
    });
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
