// Constants
var CONFERENCE_ID = '';
var SHORT_PHRASE = '';
var SUBMISSION_ID = '';
var BLIND_SUBMISSION_ID = '';
var WITHDRAWN_SUBMISSION_ID = '';
var DESK_REJECTED_SUBMISSION_ID = '';
var HEADER = {};
var LEGACY_INVITATION_ID = false;
var OFFICIAL_REVIEW_NAME = '';
var OFFICIAL_META_REVIEW_NAME = '';
var DECISION_NAME = '';
var BID_NAME = '';
var RECOMMENDATION_NAME = '';
var COMMENT_NAME = '';
var SCORES_NAME = '';
var AUTHORS_ID = '';
var REVIEWERS_ID = '';
var AREA_CHAIRS_ID = '';
var PROGRAM_CHAIRS_ID = '';
var REQUEST_FORM_ID = '';
var EMAIL_SENDER = null;

var WILDCARD_INVITATION = CONFERENCE_ID + '(/Reviewers|/Area_Chairs)?/-/.*';
var ANONREVIEWER_WILDCARD = CONFERENCE_ID + '/Paper.*/AnonReviewer.*';
var AREACHAIR_WILDCARD = CONFERENCE_ID + '/Paper.*/Area_Chairs';
var PC_PAPER_TAG_INVITATION = PROGRAM_CHAIRS_ID + '/-/Paper_Assignment';
var REVIEWERS_INVITED_ID = REVIEWERS_ID + '/Invited';
var AREA_CHAIRS_INVITED_ID = AREA_CHAIRS_ID ? AREA_CHAIRS_ID + '/Invited' : '';
var ENABLE_REVIEWER_REASSIGNMENT = false;
var PAGE_SIZE = 25;

// Page State
var reviewerSummaryMap = {};
var conferenceStatusData = {};
var pcTags = {};
var selectedNotesById = {};
var matchingNoteIds = [];
var paperStatusNeedsRerender = false;

var main = function() {
  OpenBanner.venueHomepageLink(CONFERENCE_ID);

  renderHeader();

  $.when(
    getAllReviewers(),
    getAllAreaChairs(),
    getReviewerGroups(),
    getAreaChairGroups(),
    getBlindedNotes(),
    getWithdrawnNotesCount(),
    getDeskRejectedNotesCount(),
    getOfficialReviews(),
    getMetaReviews(),
    getDecisionReviews(),
    getPcAssignmentInvitationsAndTags(),
    getBidCounts(REVIEWERS_ID),
    getBidCounts(AREA_CHAIRS_ID),
    getAreaChairRecommendationCounts(),
    getGroupMembersCount(REVIEWERS_INVITED_ID),
    getGroupMembersCount(AREA_CHAIRS_INVITED_ID),
    getRequestForm(),
    getRegistrationForms(),
    getWildcardInvitations()
  ).then(function(
    reviewers,
    areaChairs,
    reviewerGroups,
    areaChairGroups,
    blindedNotes,
    withdrawnNotesCount,
    deskRejectedNotesCount,
    officialReviews,
    metaReviews,
    decisions,
    pcAssignmentInvitationsAndTags,
    reviewerBidCounts,
    areaChairBidCounts,
    areaChairRecommendationCounts,
    reviewersInvitedCount,
    areaChairsInvitedCount,
    requestForm,
    registrationForms,
    wildcardInvitations
  ) {
    var noteNumbers = blindedNotes.map(function(note) { return note.number; });
    blindedNotes.forEach(function(n) {
      selectedNotesById[n.id] = false;
    });

    reviewerSummaryMap = buildNoteMap(noteNumbers);

    var areaChairGroupMaps = buildAreaChairGroupMaps(noteNumbers, areaChairGroups);
    var reviewerGroupMaps = buildReviewerGroupMaps(noteNumbers, reviewerGroups);
    var officialReviewMap = buildOfficialReviewMap(noteNumbers, officialReviews);

    pcAssignmentInvitationsAndTags.tags.forEach(function(tag) {
      if (!(tag.forum in pcTags)) {
        pcTags[tag.forum] = [];
      }
      pcTags[tag.forum].push(tag);
    });

    conferenceStatusData = {
      reviewers: reviewers,
      areaChairs: areaChairs,
      blindedNotes: blindedNotes,
      officialReviews: officialReviewMap,
      metaReviews: metaReviews,
      reviewerGroups: reviewerGroupMaps,
      areaChairGroups: areaChairGroupMaps,
      decisions: decisions,
      pcAssignmentTagInvitations: pcAssignmentInvitationsAndTags.invitations
    };

    var conferenceStats = {
      blindSubmissionsCount: blindedNotes.length,
      withdrawnSubmissionsCount: withdrawnNotesCount,
      deskRejectedSubmissionsCount: deskRejectedNotesCount,
      reviewersInvitedCount: reviewersInvitedCount,
      areaChairsInvitedCount: areaChairsInvitedCount,
      reviewersCount: reviewers.length,
      areaChairsCount: areaChairs.length,
      acBidsComplete: calcBidsComplete(areaChairBidCounts, 60),
      acRecsComplete: calcRecsComplete(areaChairGroupMaps.byAreaChairs, areaChairRecommendationCounts, 7),
      reviewerBidsComplete: calcBidsComplete(reviewerBidCounts, 40),
      reviewsCount: officialReviews.length,
      assignedReviewsCount: calcAssignedReviewsCount(reviewerGroupMaps.byReviewers),
      reviewersWithAssignmentsCount: Object.keys(reviewerGroupMaps.byReviewers).length,
      reviewersComplete: calcReviewersComplete(reviewerGroupMaps.byReviewers, officialReviews),
      paperReviewsComplete: calcPaperReviewsComplete(reviewerGroupMaps.byNotes, officialReviewMap),
      metaReviewsCount: metaReviews.length,
      metaReviewersComplete: calcMetaReviewersComplete(areaChairGroupMaps.byAreaChairs, metaReviews),
    };
    var conferenceConfig = {
      requestForm: requestForm,
      registrationForms: registrationForms,
      invitations: wildcardInvitations,
    };
    displayStatsAndConfiguration(conferenceStats, conferenceConfig);

    var uniqueIds = _.union(reviewers, areaChairs);
    return getUserProfiles(uniqueIds, reviewerBidCounts, areaChairBidCounts, areaChairRecommendationCounts);
  })
  .then(function(profiles) {
    conferenceStatusData.profiles = profiles;

    conferenceStatusData.blindedNotes
    for (var i = 0; i < conferenceStatusData.blindedNotes.length; i++) {
      var note = conferenceStatusData.blindedNotes[i];
      var revIds = conferenceStatusData.reviewerGroups.byNotes[note.number];
      for (var revNumber in revIds) {
        var id = revIds[revNumber];
        if (!id.id) {
          revIds[revNumber] = findProfile(profiles, id);
        }
      }
    }

    conferenceStatusData.reviewerOptions = _.map(conferenceStatusData.reviewers, function(r) {
      var profile = findProfile(conferenceStatusData.profiles, r);
      return {
        id: r,
        description: view.prettyId(profile.name) + ' (' + profile.allEmails.join(', ') + ')'
      }
    });

    $('.tabs-container .nav-tabs > li').removeClass('loading');
    Webfield.ui.done();
  })
  .fail(function() {
    displayError();
  });
};


// Ajax functions
var getRequestForm = function() {
  if (!REQUEST_FORM_ID) {
    return $.Deferred().resolve(null);
  }

  return Webfield.get('/notes', { id: REQUEST_FORM_ID, limit: 1 }, { handleErrors: false })
  .then(function(result) {
    return _.get(result, 'notes[0]', null);
  }, function() {
    // Do not fail if config note cannot be loaded
    return $.Deferred().resolve(null);
  });
};

var getRegistrationForms = function() {
  return Webfield.getAll('/notes', {
    invitation: CONFERENCE_ID + '/.*/-/Form'
  });
};

var getWildcardInvitations = function() {
  return Webfield.getAll('/invitations', {
    regex: WILDCARD_INVITATION,
    expired: true,
    type: 'all'
  });
};

var getAllReviewers = function() {
  return Webfield.get('/groups', { id: REVIEWERS_ID, limit: 1 })
  .then(function(result) {
    var members = _.get(result, 'groups[0].members', []);
    return members.sort();
  });
};

var getAllAreaChairs = function() {
  if (!AREA_CHAIRS_ID) {
    return $.Deferred().resolve([]);
  }

  return Webfield.get('/groups', { id: AREA_CHAIRS_ID, limit: 1 })
  .then(function(result) {
    var members = _.get(result, 'groups[0].members', []);
    return members.sort();
  });
};

var getBlindedNotes = function() {
  return Webfield.getAll('/notes', {
    invitation: BLIND_SUBMISSION_ID, sort: 'number:asc'
  });
};

var getWithdrawnNotesCount = function() {
  if (!WITHDRAWN_SUBMISSION_ID) {
    return $.Deferred().resolve(0);
  }
  return Webfield.get('/notes', {
    invitation: WITHDRAWN_SUBMISSION_ID, limit: 1
  }).then(function(result) {
    return result.count || 0;
  });
};

var getDeskRejectedNotesCount = function() {
  if (!DESK_REJECTED_SUBMISSION_ID) {
    return $.Deferred().resolve(0);
  }
  return Webfield.get('/notes', {
    invitation: DESK_REJECTED_SUBMISSION_ID, limit: 1
  }).then(function(result) {
    return result.count || 0;
  });
};

var getOfficialReviews = function() {
  return Webfield.getAll('/notes', {
    invitation: getInvitationId(OFFICIAL_REVIEW_NAME, '.*')
  });
};

var getReviewerGroups = function() {
  return Webfield.getAll('/groups', { id: ANONREVIEWER_WILDCARD });
};

var getAreaChairGroups = function() {
  if (!AREA_CHAIRS_ID) {
    return $.Deferred().resolve([]);
  }

  return Webfield.getAll('/groups', {
    id: AREACHAIR_WILDCARD
  });
};

var getUserProfiles = function(userIds, reviewerBidCounts, areaChairBidCounts, areaChairRecommendationCounts) {
  reviewerBidCounts = reviewerBidCounts || {};
  areaChairBidCounts = areaChairBidCounts || {};
  areaChairRecommendationCounts = areaChairRecommendationCounts || {};

  var ids = _.filter(userIds, function(id) { return id.charAt(0) === '~'; });
  var emails = _.filter(userIds, function(id) { return id.indexOf('@') > 0; });

  var idSearch = ids.length ?
    Webfield.post('/profiles/search', { ids: ids }) :
    $.Deferred().resolve([]);

  var emailSearch = emails.length ?
    Webfield.post('/profiles/search', { emails: emails }) :
    $.Deferred().resolve([]);

  return $.when(idSearch, emailSearch)
    .then(function(idResults, emailResults) {
      idResults = idResults.profiles || [];
      emailResults = emailResults.profiles || [];
      var searchResults = idResults.concat(emailResults);

      return searchResults.reduce(function(profileMap, profile) {
        var name = _.find(profile.content.names, ['preferred', true]) || _.first(profile.content.names);
        name = name ?
          [name.first, name.middle, name.last].filter(_.identity).join(' ') :
          view.prettyId(profile.id);

        profileMap[profile.id] = {
          id: profile.id,
          name: name,
          allNames: _.map(_.filter(profile.content.names, function(name) { return name.username; }), 'username'),
          email: profile.content.preferredEmail || profile.content.emailsConfirmed[0],
          allEmails: profile.content.emailsConfirmed,
          bidCount: reviewerBidCounts[profile.id] || areaChairBidCounts[profile.id] || 0,
          acRecommendationCount: areaChairRecommendationCounts[profile.id] || 0
        };
        return profileMap;
      }, {});
    });
};

var getMetaReviews = function() {
  if (!AREA_CHAIRS_ID ) {
    return $.Deferred().resolve([]);
  }

  return Webfield.getAll('/notes', {
    invitation: getInvitationId(OFFICIAL_META_REVIEW_NAME, '.*')
  });
};

var getDecisionReviews = function() {
  return Webfield.getAll('/notes', {
    invitation: getInvitationId(DECISION_NAME, '.*')
  });
};

var getPcAssignmentInvitationsAndTags = function() {
  var invitationsAndTags = { invitations: [], tags: [] };

  return Webfield.getAll('/invitations', {
    regex: PC_PAPER_TAG_INVITATION, tags: true
  })
  .then(function(invitations) {
    invitationsAndTags.invitations = invitations;

    if (!invitations.length) {
      return $.Deferred().resolve([]);
    }
    return Webfield.getAll('/tags', { invitation: PC_PAPER_TAG_INVITATION })
  })
  .then(function(tags) {
    invitationsAndTags.tags = tags;
    return invitationsAndTags;
  });
};

var postReviewerEmails = function(postData) {
  var formttedData = _.pick(postData, ['groups', 'subject', 'message']);
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

var getBidCounts = function(bidInvitationGroup) {
  if (!bidInvitationGroup || !BID_NAME) {
    return $.Deferred().resolve({});
  }

  return Webfield.getAll('/edges', {
    invitation: bidInvitationGroup + '/-/' + BID_NAME,
    groupBy: 'tail',
    select: 'count'
  }, 'groupedEdges').then(function(results) {
    if (!results || !results.length) {
      return {};
    }
    return results.reduce(function(profileMap, groupedEdge) {
      profileMap[groupedEdge.id.tail] = groupedEdge.count;
      return profileMap;
    }, {});
  });
};

var getAreaChairRecommendationCounts = function() {
  if (!RECOMMENDATION_NAME || !AREA_CHAIRS_ID) {
    return $.Deferred().resolve({});
  }

  // Can't perform a groupBy query on signatures, so we have to get the full list
  return Webfield.getAll('/edges', {
    invitation: REVIEWERS_ID + '/-/' + RECOMMENDATION_NAME,
  }).then(function(edges) {
    if (!edges || !edges.length) {
      return {};
    }
    return edges.reduce(function(profileMap, edge) {
      var acId = edge.signatures[0];
      if (!profileMap[acId]) {
        profileMap[acId] = 0
      }
      profileMap[acId] += 1
      return profileMap;
    }, {});
  });
};

var getGroupMembersCount = function(invitationId) {
  if (!invitationId) {
    return $.Deferred().resolve(0);
  }

  return Webfield.get('/groups', { id: invitationId, limit: 1 }, { handleErrors: false })
    .then(function(result) {
      var members = _.get(result, 'groups[0].members', []);
      return members.length;
    }, function() {
      // Do not fail if group cannot be retreived
      return $.Deferred().resolve(0);
    });
};


// Util functions
var getNumberfromGroup = function(groupId, name) {
  var tokens = groupId.split('/');
  var paper = _.find(tokens, function(token) {
    return _.startsWith(token, name);
  });

  return paper ? parseInt(paper.replace(name, ''), 10) : null;
};

var getPaperNumbersfromGroups = function(groups) {
  return _.filter(_.map(groups, function(group) {
    return getNumberfromGroup(group.id, 'Paper');
  }), _.isInteger);
};

var getInvitationId = function(name, number) {
  if (LEGACY_INVITATION_ID) {
    return CONFERENCE_ID + '/-/Paper' + number + '/' + name;
  }
  return CONFERENCE_ID + '/Paper' + number + '/-/' + name;
};

var findNextAnonGroupNumber = function(paperNumber) {
  var paperReviewerNums = Object.keys(reviewerSummaryMap[paperNumber].reviewers).sort();
  for (var i = 1; i < paperReviewerNums.length + 1; i++) {
    if (i.toString() !== paperReviewerNums[i - 1]) {
      return i;
    }
  }
  return paperReviewerNums.length + 1;
};

var findProfile = function(profiles, id) {
  if (profiles[id]) {
    return profiles[id];
  }
  var profile = _.find(profiles, function(p) {
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

var buildAreaChairGroupMaps = function(noteNumbers, groups) {
  var noteMap = buildNoteMap(noteNumbers);
  var areaChairMap = {};

  groups.forEach(function(g) {
    var num = getNumberfromGroup(g.id, 'Paper');
    if (!num) {
      return;
    }

    var areaChair = _.find(g.members, function(member) {
      return member.indexOf('~') > -1 || member.indexOf('@') > -1;
    });
    if (!areaChair) {
      return;
    }

    if (num in noteMap) {
      noteMap[num][0] = areaChair;
    }
    if (!(areaChair in areaChairMap)) {
      areaChairMap[areaChair] = [];
    }
    areaChairMap[areaChair].push(num);
  });

  return {
    byNotes: noteMap,
    byAreaChairs: areaChairMap
  };
};

var buildOfficialReviewMap = function(noteNumbers, notes) {
  if (!noteNumbers || !noteNumbers.length) {
    return $.Deferred().resolve({});
  }

  var noteMap = buildNoteMap(noteNumbers);
  if (!notes || !notes.length) {
    return noteMap;
  }

  var ratingExp = /^(\d+): .*/;
  notes.forEach(function(n) {
    if (n.signatures[0].charAt(0) === '~') {
      var num = getNumberfromGroup(n.invitation, 'Paper');
      var index = n.signatures[0];
    } else {
      var num = getNumberfromGroup(n.signatures[0], 'Paper');
      var index = getNumberfromGroup(n.signatures[0], 'AnonReviewer');
    }

    if (num && num in noteMap) {
      ratingMatch = n.content.rating && n.content.rating.match(ratingExp);
      n.rating = ratingMatch ? parseInt(ratingMatch[1], 10) : null;
      confidenceMatch = n.content.confidence && n.content.confidence.match(ratingExp);
      n.confidence = confidenceMatch ? parseInt(confidenceMatch[1], 10) : null;
      noteMap[num][index] = n;
    }
  });

  return noteMap;
};

var buildReviewerGroupMaps = function(noteNumbers, groups) {
  var noteMap = buildNoteMap(noteNumbers);
  var reviewerMap = {};

  _.forEach(groups, function(g) {
    var num = getNumberfromGroup(g.id, 'Paper');
    var index = getNumberfromGroup(g.id, 'AnonReviewer');
    if (num) {
      if (g.members.length) {
        var reviewer = g.members[0];
        if ((num in noteMap)) {
          noteMap[num][index] = reviewer;
        }

        if (!(reviewer in reviewerMap)) {
          reviewerMap[reviewer] = [];
        }

        reviewerMap[reviewer].push(num);
      }
    }
  });

  return {
    byNotes: noteMap,
    byReviewers: reviewerMap
  };
};

var buildEdgeBrowserUrl = function(startQuery, invGroup, invName) {
  var invitationId = invGroup + '/-/' + invName;
  var referrerUrl = '/group' + location.search + location.hash;

  // Right now this is only showing bids, affinity scores, and conflicts as the
  // other scores invitations + labels are not available in the PC console
  return '/edge/browse' +
    (startQuery ? '?start=' + invitationId + ',' + startQuery + '&' : '?') +
    'traverse=' + invitationId +
    '&browse=' + invitationId +
    (SCORES_NAME ? ';' + invGroup + '/-/' + SCORES_NAME : '') +
    ';' + invGroup + '/-/Conflict' +
    '&referrer=' + encodeURIComponent('[PC Console](' + referrerUrl + ')');
};

var calcBidsComplete = function(bidCounts, taskCompletionCount) {
  // Count how many reviewers or AC have submitted the required number of bids
  return _.reduce(bidCounts, function(numComplete, bidCount) {
    return bidCount >= taskCompletionCount ? numComplete + 1 : numComplete;
  }, 0);
};

var calcRecsComplete = function(acMap, areaChairRecommendationCounts, taskCompletionCount) {
  // Count how many ACs have submitted the required number of reviewer recommendations
  // NOTE: this is not checking that each assigned paper has the required number of rec,
  // it is just multiplying the number required by the number of assigned papers
  return _.reduce(areaChairRecommendationCounts, function(numComplete, bidCount, profileId) {
    return (!acMap[profileId] || bidCount >= acMap[profileId].length * taskCompletionCount)
      ? numComplete + 1
      : numComplete;
  }, 0);
};

var calcAssignedReviewsCount = function(reviewerMap) {
  return _.reduce(reviewerMap, function(numComplete, noteNumbers) {
    return numComplete + noteNumbers.length;
  }, 0);
};

var calcReviewersComplete = function(reviewerMap, officialReviews) {
  return _.reduce(reviewerMap, function(numComplete, noteNumbers) {
    var allSubmitted = _.every(noteNumbers, function(n) {
      return _.find(officialReviews, ['invitation', getInvitationId(OFFICIAL_REVIEW_NAME, n)]);
    });
    return allSubmitted ? numComplete + 1 : numComplete;
  }, 0);
};

var calcPaperReviewsComplete = function(noteMap, officialReviewMap) {
  return _.reduce(noteMap, function(numComplete, reviewerMap, n) {
    var reviewerCount = Object.values(reviewerMap).length;
    var allSubmitted = officialReviewMap[n] && reviewerCount > 0 && reviewerCount === Object.values(officialReviewMap[n]).length;
    return allSubmitted ? numComplete + 1 : numComplete;
  }, 0);
};

var calcMetaReviewersComplete = function(acMap, metaReviews) {
  return _.reduce(acMap, function(numComplete, noteNumbers) {
    var allSubmitted = _.every(noteNumbers, function(n) {
      return _.find(metaReviews, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, n)]);
    });
    return allSubmitted ? numComplete + 1 : numComplete;
  }, 0);
};


// Render functions
var renderHeader = function() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);
  Webfield.ui.header(HEADER.title, '');

  var loadingMessage = '<p class="empty-message">Loading...</p>';
  var tabs = [
    {
      heading: 'Overview',
      id: 'venue-configuration',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll',
      active: true
    },
    {
      heading: 'Paper Status',
      id: 'paper-status',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll'
    }
  ];

  if (AREA_CHAIRS_ID) {
    tabs.push({
      heading: 'Area Chair Status',
      id: 'areachair-status',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll'
    });
  }

  tabs.push({
    heading: 'Reviewer Status',
    id: 'reviewer-status',
    content: loadingMessage,
    extraClasses: 'horizontal-scroll'
  });

  Webfield.ui.tabPanel(tabs);
  $('.tabs-container .nav-tabs > li').not(':first-child').addClass('loading');
};

var displayStatsAndConfiguration = function(conferenceStats, conferenceConfig) {
  var referrerUrl = encodeURIComponent('[Program Chair Console](/group?id=' + CONFERENCE_ID + '/Program_Chairs)');
  var formatPeriod = function(invitation) {
    var start;
    var end;
    var exp = 'never';
    var afterStart = true;
    var beforeEnd = true;
    var now = Date.now();
    if (invitation.cdate) {
      var date = new Date(invitation.cdate);
      start =  date.toLocaleDateString('en-GB', { hour: 'numeric', minute: 'numeric', day: '2-digit', month: 'short', year: 'numeric', timeZoneName: 'short'});
      afterStart = now > invitation.cdate;
    }
    if (invitation.duedate) {
      var date = new Date(invitation.duedate);
      end =  date.toLocaleDateString('en-GB', { hour: 'numeric', minute: 'numeric', day: '2-digit', month: 'short', year: 'numeric', timeZoneName: 'short'});
      beforeEnd = now < invitation.duedate;
    }
    if (invitation.expdate) {
      var date = new Date(invitation.expdate);
      exp =  date.toLocaleDateString('en-GB', { hour: 'numeric', minute: 'numeric', day: '2-digit', month: 'short', year: 'numeric', timeZoneName: 'short'});
    }

    var periodString = start ? 'from <em>' + start + '</em> ' : 'open ';
    if (end) {
      periodString = periodString + 'until <em>' + end + '</em> and expires <em>' + exp + '</em>';
    } else {
      periodString = periodString + 'no deadline' + ' and expires <em>' + exp + '</em>';
    }

    return periodString;
  };

  var renderInvitation = function(invitationMap, id, name) {
    var invitation = invitationMap[id];

    if (invitation) {
      return '<li><a href="/invitation?id=' + invitation.id + '&referrer=' + referrerUrl + '">' + name + '</a> ' + formatPeriod(invitation) + '</li>';
    };
    return '';
  };

  var getConfigurationDescription = function(note) {
    var description = [
      'Author And Reviewer Anonymity: ' + note.content['Author and Reviewer Anonymity'],
      note.content['Open Reviewing Policy'],
      note.content['Public Commentary'],
      'Paper matching uses ' + note.content['Paper Matching'].join(', ')
    ];
    if (note.content['Other Important Information']) {
      description.push(note.content['Other Important Information']);
    }
    return description.join('<br>').replace(/should be/g, 'are');
  };

  var renderProgressStat = function(numComplete, numTotal) {
    if (numTotal === 0) {
      return '<h3><span style="color: #777;">' + numComplete + ' / 0</span></h3>'
    }
    return '<h3>' +
      _.round((numComplete / numTotal) * 100, 1) + '% &nbsp;' +
      '<span style="color: #777;">(' + numComplete + ' / ' + numTotal + ')</span>' +
    '</h3>';
  };

  var renderStatContainer = function(title, stat, hint) {
    return '<div class="col-md-4 col-xs-6">' +
      '<h4>' + title + '</h4>' +
      (hint ? '<p class="hint">' + hint + '</p>' : '') + stat +
      '</div>';
  };

  // Conference statistics
  var html = '<div class="row" style="margin-left: -15px; margin-right: -15px; margin-top: .5rem;">';
  html += renderStatContainer(
    'Reviewer Recruitment:',
    '<h3>' + conferenceStats.reviewersCount + ' / ' + conferenceStats.reviewersInvitedCount + '</h3>',
    'accepted / invited'
  );
  if (AREA_CHAIRS_ID) {
    html += renderStatContainer(
      'Area Chair Recruitment:',
      '<h3>' + conferenceStats.areaChairsCount + ' / ' + conferenceStats.areaChairsInvitedCount + '</h3>',
      'accepted / invited'
    );
  }
  html += '</div>';
  html += '<hr class="spacer" style="margin-bottom: 1rem;">';

  html += '<div class="row" style="margin-left: -15px; margin-right: -15px; margin-top: .5rem;">';
  html += renderStatContainer(
    'Active Submissions:',
    '<h3>' + conferenceStats.blindSubmissionsCount + '</h3>'
  );
  html += renderStatContainer(
    'Withdrawn Submissions:',
    '<h3>' + conferenceStats.withdrawnSubmissionsCount + '</h3>'
  );
  html += renderStatContainer(
    'Desk Rejected Submissions:',
    '<h3>' + conferenceStats.deskRejectedSubmissionsCount + '</h3>'
  );
  html += '</div>';
  html += '<hr class="spacer" style="margin-bottom: 1rem;">';

  if (BID_NAME || RECOMMENDATION_NAME) {
    html += '<div class="row" style="margin-left: -15px; margin-right: -15px; margin-top: .5rem;">';
    if (BID_NAME) {
      html += renderStatContainer(
        'AC Bidding Progress:',
        renderProgressStat(conferenceStats.acBidsComplete, conferenceStats.areaChairsCount),
        '% of ACs who have completed the required number of bids'
      );
    }
    if (RECOMMENDATION_NAME) {
      html += renderStatContainer(
        'Recommendation Progress:',
        renderProgressStat(conferenceStats.acRecsComplete, conferenceStats.areaChairsCount),
        '% of ACs who have completed the required number of reviewer recommendations'
      );
    }
    if (BID_NAME) {
      html += renderStatContainer(
        'Reviewer Bidding Progress:',
        renderProgressStat(conferenceStats.reviewerBidsComplete, conferenceStats.reviewersCount),
        '% of Reviewers who have completed the required number of bids'
      );
    }
    html += '</div>';
    html += '<hr class="spacer" style="margin-bottom: 1rem;">';
  }

  html += '<div class="row" style="margin-left: -15px; margin-right: -15px; margin-top: .5rem;">';
  html += renderStatContainer(
    'Review Progress:',
    renderProgressStat(conferenceStats.reviewsCount, conferenceStats.assignedReviewsCount),
    '% of all assigned official reviews that have been submitted'
  );
  html += renderStatContainer(
    'Reviewer Progress:',
    renderProgressStat(conferenceStats.reviewersComplete, conferenceStats.reviewersWithAssignmentsCount),
    '% of reviewers who have reviewed all of their assigned papers'
  );
  html += renderStatContainer(
    'Paper Progress:',
    renderProgressStat(conferenceStats.paperReviewsComplete, conferenceStats.blindSubmissionsCount),
    '% of papers that have received reviews from all assigned reviewers'
  );
  html += '</div>';
  html += '<hr class="spacer" style="margin-bottom: 1rem;">';

  if (AREA_CHAIRS_ID) {
    html += '<div class="row" style="margin-left: -15px; margin-right: -15px; margin-top: .5rem;">';
    html += renderStatContainer(
      'Meta-Review Progress:',
      renderProgressStat(conferenceStats.metaReviewsCount, conferenceStats.blindSubmissionsCount),
      '% of papers that have received meta-reviews'
    );
    html += renderStatContainer(
      'AC Meta-Review Progress:',
      renderProgressStat(conferenceStats.metaReviewersComplete, conferenceStats.areaChairsCount),
      '% of area chairs who have completed meta reviews for all their assigned papers'
    );
    html += '</div>';
    html += '<hr class="spacer" style="margin-bottom: 1rem;">';
  }

  // Config
  var requestForm = conferenceConfig.requestForm;
  html += '<div class="row" style="margin-left: -15px; margin-right: -15px; margin-top: .5rem;">';
  if (requestForm) {
    html += '<div class="col-md-4 col-xs-12">'
    html += '<h4>Description:</h4>';
    html += '<p style="margin-bottom:2rem"><span>' + getConfigurationDescription(requestForm) + '</span><br>' +
      '<a href="/forum?id=' + requestForm.id + '"><strong>Full Venue Configuration</strong></a>'
      '</p>';
    html += '</div>';
  }

  // Timeline
  var invitationMap = {};
  conferenceConfig.invitations.forEach(function(invitation) {
    invitationMap[invitation.id] = invitation;
  });

  html += '<div class="col-md-8 col-xs-12">'
  html += '<h4>Timeline:</h4><ul style="padding-left: 15px">';
  html += renderInvitation(invitationMap, SUBMISSION_ID, 'Paper Submissions')
  html += renderInvitation(invitationMap, REVIEWERS_ID + '/-/' + BID_NAME, 'Reviewers Bidding')
  if (AREA_CHAIRS_ID) {
    html += renderInvitation(invitationMap, AREA_CHAIRS_ID + '/-/' + BID_NAME, 'Area Chairs Bidding')
    html += renderInvitation(invitationMap, REVIEWERS_ID + '/-/Recommendation', 'Reviewer Recommendation')
    html += '<li><a href="/assignments?group=' + AREA_CHAIRS_ID + '&referrer=' + referrerUrl + '">Area Chairs Paper Assignment</a> open until Reviewing starts</li>';
  }
  html += '<li><a href="/assignments?group=' + REVIEWERS_ID + '&referrer=' + referrerUrl + '">Reviewers Paper Assignment</a> open until Reviewing starts</li>';
  html += renderInvitation(invitationMap, CONFERENCE_ID + '/-/' + OFFICIAL_REVIEW_NAME, 'Reviewing')
  html += renderInvitation(invitationMap, CONFERENCE_ID + '/-/' + COMMENT_NAME, 'Commenting')
  html += renderInvitation(invitationMap, CONFERENCE_ID + '/-/' + OFFICIAL_META_REVIEW_NAME, 'Meta Reviews')
  html += renderInvitation(invitationMap, CONFERENCE_ID + '/-/' + DECISION_NAME, 'Decisions')
  html += '</ul>';
  html += '</div>';
  html += '</div>';

  // Official Committee
  html += '<div class="row" style="margin-left: -15px; margin-right: -15px; margin-top: .5rem;">';
  html += '<div class="col-md-4 col-xs-6">'
  html += '<h4>Venue Roles:</h4><ul style="padding-left: 15px">' +
    '<li><a href="/group?id=' + PROGRAM_CHAIRS_ID + '&mode=edit">Program Chairs</a></li>';
  if (AREA_CHAIRS_ID) {
    html += '<li><a href="/group?id=' + AREA_CHAIRS_ID + '&mode=edit">Area Chairs</a> (' +
      '<a href="/group?id=' + AREA_CHAIRS_ID + '/Invited&mode=edit">Invited</a>, ' +
      '<a href="/group?id=' + AREA_CHAIRS_ID + '/Declined&mode=edit">Declined</a>)</li>';
  }
  html += '<li><a href="/group?id=' + REVIEWERS_ID + '&mode=edit">Reviewers</a> (' +
    '<a href="/group?id=' + REVIEWERS_ID + '/Invited&mode=edit">Invited</a>, ' +
    '<a href="/group?id=' + REVIEWERS_ID + '/Declined&mode=edit">Declined</a>)</li>' +
    '<li><a href="/group?id=' + AUTHORS_ID + '&mode=edit">Authors</a></li></ul>';
  html += '</div>';

  // Registration Forms
  var registrationForms = conferenceConfig.registrationForms;
  if (registrationForms && registrationForms.length) {
    html += '<div class="col-md-4 col-xs-6">'
    html += '<h4>Registration Forms:</h4><ul style="padding-left: 15px">';
    registrationForms.forEach(function(form) {
      html += '<li><a href="/forum?id=' + form.forum + '">' + form.content.title + '</a></li>';
    })
    html += '</ul>';
    html += '</div>';
  }

  // Bids and Recommendations
  if (BID_NAME) {
    html += '<div class="col-md-4 col-xs-6">'
    html += '<h4>Bids & Recommendations:</h4><ul style="padding-left: 15px">';
    html += '<li><a href="' + buildEdgeBrowserUrl(null, REVIEWERS_ID, BID_NAME) + '">Reviewer Bids</a></li>';
    html += '<li><a href="' + buildEdgeBrowserUrl(null, AREA_CHAIRS_ID, BID_NAME) + '">Area Chair Bids</a></li>';
    if (RECOMMENDATION_NAME) {
      html += '<li><a href="' + buildEdgeBrowserUrl(null, REVIEWERS_ID, RECOMMENDATION_NAME) + '">Area Chair Reviewer Recommendations</a></li>';
    }
    html += '</ul>';
    html += '</div>';
  }
  html += '</div>';

  $('#venue-configuration').html(html);
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

var addTagsToPaperSummaryCell = function(data, pcAssignmentTagInvitations) {
  if (!pcAssignmentTagInvitations || !pcAssignmentTagInvitations.length) {
    return;
  }
  var tagInvitation = pcAssignmentTagInvitations[0];

  _.forEach(data, function(d) {
    $noteSummaryContainer = $('#note-summary-' + d.note.number);
    if (!$noteSummaryContainer.length) {
      return;
    }

    var paperTags = pcTags[d.note.forum] ? pcTags[d.note.forum] : [];
    var $tagWidget = view.mkTagInput(
      'tag',
      tagInvitation && tagInvitation.reply.content.tag,
      paperTags,
      {
        forum: d.note.id,
        placeholder: (tagInvitation && tagInvitation.reply.content.tag.description) || (tagInvitation && prettyId(tagInvitation.id)),
        label: tagInvitation && view.prettyInvitationId(tagInvitation.id),
        readOnly: false,
        onChange: function(id, value, deleted, done) {
          var body = {
            id: id,
            tag: value,
            signatures: [PROGRAM_CHAIRS_ID],
            readers: [PROGRAM_CHAIRS_ID],
            forum: d.note.id,
            invitation: tagInvitation.id,
            ddate: deleted ? Date.now() : null
          };
          body = view.getCopiedValues(body, tagInvitation.reply);
          Webfield.post('/tags', body)
          .then(function(result) {
            done(result);
          })
          .fail(function(error) {
            promptError(error ? error : 'The specified tag could not be updated');
          });
        }
      }
    );
    $noteSummaryContainer.append($tagWidget);
  });
}

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


var displayPaperStatusTable = function() {

  var container = '#paper-status';
  var profiles = conferenceStatusData.profiles;
  var notes = conferenceStatusData.blindedNotes;
  var completedReviews = conferenceStatusData.officialReviews;
  var metaReviews = conferenceStatusData.metaReviews;
  var reviewerIds = conferenceStatusData.reviewerGroups.byNotes;
  var areachairIds = conferenceStatusData.areaChairGroups.byNotes;
  var decisions = conferenceStatusData.decisions;
  var pcAssignmentTagInvitations = conferenceStatusData.pcAssignmentTagInvitations;

  var rowData = _.map(notes, function(note) {
    var revIds = reviewerIds[note.number];
    var areachairId = areachairIds[note.number][0];
    var areachairProfile = {}
    if (areachairId) {
      areachairProfile = findProfile(profiles, areachairId);
    } else {
      areachairProfile.name = view.prettyId(CONFERENCE_ID + '/Paper' + note.number + '/Area_Chairs');
      areachairProfile.email = '-';
    }
    var metaReview = _.find(metaReviews, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, note.number)]);
    var decision = _.find(decisions, ['invitation', getInvitationId(DECISION_NAME, note.number)]);
    return buildPaperTableRow(note, revIds, completedReviews[note.number], metaReview, areachairProfile, decision);
  });

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
    Average_Confidence: function(row) { return toNumber(row.reviewProgressData.averageConfidence); },
    Max_Confidence: function(row) { return toNumber(row.reviewProgressData.maxConfidence); },
    Min_Confidence: function(row) { return toNumber(row.reviewProgressData.minConfidence); },
    Reviewers_Assigned: function(row) { return row.reviewProgressData.numReviewers; },
    Reviews_Submitted: function(row) { return row.reviewProgressData.numSubmittedReviews; },
    Reviews_Missing: function(row) { return row.reviewProgressData.numReviewers - row.reviewProgressData.numSubmittedReviews; }
  };
  if (AREA_CHAIRS_ID) {
    sortOptions['Meta_Review_Missing'] = function(row) { return row.areachairProgressData.numMetaReview; }
  }
  sortOptions['Decision'] = function(row) { return row.decision ? row.decision.content.decision : 'No Decision'; }
  if (pcAssignmentTagInvitations && pcAssignmentTagInvitations.length) {
    sortOptions['Papers_Assigned_to_Me'] = function(row) {
      var tags = pcTags[row.note.id];
      return (tags && tags.length && tags[0].tag === view.prettyId(user.profile.id));
    };
  }

  var sortResults = function(newOption, switchOrder) {
    $(container + ' .form-search').val('');

    if (switchOrder) {
      order = order === 'asc' ? 'desc' : 'asc';
    }
    rowData = _.orderBy(rowData, sortOptions[newOption], order);
    renderTable(container, rowData);
  };

  var searchResults = function(searchText) {
    $(container).data('lastPageNum', 1);
    $(container + ' .form-sort').val('Paper_Number');

    // Currently only searching on note number and note title
    var filterFunc = function(row) {
      return (
        (row.note.number + '').indexOf(searchText) === 0 ||
        row.note.content.title.toLowerCase().indexOf(searchText) !== -1
      );
    };

    var filteredRows;
    if (searchText) {
      filteredRows = _.orderBy(_.filter(rowData, filterFunc), sortOptions['Paper_Number'], 'asc');
      matchingNoteIds = filteredRows.map(function(row) { return row.note.id; });
    } else {
      filteredRows = rowData;
      matchingNoteIds = [];
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
      '\n\nThank you,\n' + SHORT_PHRASE + ' Program Chair';

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
    $('.console-table th').eq(0).css('width', '3%');
    $('.console-table th').eq(1).css('width', '5%');
    $('.console-table th').eq(2).css('width', '22%');
    if (AREA_CHAIRS_ID) {
      $('.console-table th').eq(3).css('width', '30%');
      $('.console-table th').eq(4).css('width', '28%');
      $('.console-table th').eq(5).css('width', '12%');
    } else {
      $('.console-table th').eq(3).css('width', '45%');
      $('.console-table th').eq(4).css('width', '25%');
    }

    var offset = (pageNum - 1) * PAGE_SIZE;
    var pageData = data.slice(offset, offset + PAGE_SIZE);

    if (ENABLE_REVIEWER_REASSIGNMENT) {
      pageData.forEach(function(rowData) {
        updateReviewerContainer(rowData.note.number);
      });
    }

    addTagsToPaperSummaryCell(pageData, pcAssignmentTagInvitations);

    $(container + ' .console-table > tbody > tr .select-note-reviewers').each(function() {
      var noteId = $(this).data('noteId');
      $(this).prop('checked', selectedNotesById[noteId]);
    });

    var allSelected = _.every(Object.values(selectedNotesById));
    $(container + ' .console-table #select-all-papers').prop('checked', allSelected);
  };

  if (rowData.length) {
    displaySortPanel(container, sortOptions, sortResults, searchResults);
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
    '</div>');
    renderTable(container, rowData);
  } else {
    $(container).empty().append('<p class="empty-message">No papers have been submitted. ' +
      'Check back later or contact info@openreview.net if you believe this to be an error.</p>');
  }
  paperStatusNeedsRerender = false;

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

var displayAreaChairsStatusTable = function() {
  var container = '#areachair-status';
  var notes = conferenceStatusData.blindedNotes
  var completedReviews = conferenceStatusData.officialReviews;
  var metaReviews = conferenceStatusData.metaReviews;
  var reviewerIds = conferenceStatusData.reviewerGroups.byNotes;
  var areachairIds = conferenceStatusData.areaChairGroups.byAreaChairs;

  var rowData = [];
  _.forEach(conferenceStatusData.areaChairs, function(areaChair, index) {
    var numbers = areachairIds[areaChair];
    var papers = [];
    _.forEach(numbers, function(number) {
      var note = _.find(notes, ['number', number]);
      if (!note) {
        return;
      }

      var reviewers = reviewerIds[number];
      var reviews = completedReviews[number];
      var metaReview = _.find(metaReviews, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, number)]);
      papers.push({
        note: note,
        reviewers: reviewers,
        reviews: reviews,
        metaReview: metaReview
      });
    });

    var areaChairProfile = findProfile(conferenceStatusData.profiles, areaChair);
    rowData.push(buildSPCTableRow(index + 1, areaChairProfile, papers));
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
      message: message
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
        (BID_NAME ? '<li><a class="msg-no-bids">Area Chairs with 0 bids</a></li>' : '') +
        (RECOMMENDATION_NAME ? '<li><a class="msg-no-recs">Area Chairs with 0 recommendations</a></li>' : '') +
        '<li><a class="msg-unsubmitted-reviews">Area Chairs with unsubmitted reviews</a></li>' +
        '<li><a class="msg-unsubmitted-metareviews">Area Chairs with unsubmitted meta reviews</a></li>' +
      '</ul>' +
    '</div>'
  );
  renderTable(container, rowData);
};

var displayReviewerStatusTable = function() {
  var container = '#reviewer-status';
  var notes = conferenceStatusData.blindedNotes;
  var completedReviews = conferenceStatusData.officialReviews;
  var metaReviews = conferenceStatusData.metaReviews;
  var reviewerByNote = conferenceStatusData.reviewerGroups.byNotes;
  var reviewerById = conferenceStatusData.reviewerGroups.byReviewers;

  var findReview = function(reviews, profile) {
    var found;
    profile.allNames.forEach(function(name) {
      if (reviews[name]) {
        found = reviews[name];
      }
    })
    return found;
  }

  var rowData = [];
  _.forEach(conferenceStatusData.reviewers, function(reviewer, index) {
    var numbers = reviewerById[reviewer];
    var reviewerProfile = findProfile(conferenceStatusData.profiles, reviewer);

    var papers = [];
    _.forEach(numbers, function(number) {
      var note = _.find(notes, ['number', number]);
      if (!note) {
        return;
      }

      var reviewerNum = 0;
      var reviewers = reviewerByNote[number];
      for (var revNumber in reviewers) {
        var profile = reviewers[revNumber];
        if (_.includes(profile.allNames, reviewer) || _.includes(profile.allEmails, reviewer)) {
          reviewerNum = revNumber;
          break;
        }
      }

      var reviews = completedReviews[number];
      var review = reviews[reviewerNum] || findReview(reviews, reviewerProfile);
      var metaReview = _.find(metaReviews, ['invitation', getInvitationId(OFFICIAL_META_REVIEW_NAME, number)]);

      papers.push({
        note: note,
        review: review,
        reviewers: reviewers,
        reviews: reviews,
        metaReview: metaReview
      });
    });

    rowData.push(buildPCTableRow(index + 1, reviewerProfile, papers));
  });

  var order = 'asc';
  var sortOptions = {
    Reviewer_Name: function(row) { return row.summary.name.toLowerCase(); },
    Bids_Completed: function(row) { return row.summary.completedBids },
    Papers_Assigned: function(row) { return row.reviewProgressData.numPapers; },
    Papers_with_Reviews_Missing: function(row) { return row.reviewProgressData.numPapers - row.reviewProgressData.numCompletedReviews; },
    Papers_with_Reviews_Submitted: function(row) { return row.reviewProgressData.numCompletedReviews; },
    Papers_with_Completed_Reviews_Missing: function(row) { return row.reviewStatusData.numPapers - row.reviewStatusData.numCompletedReviews; },
    Papers_with_Completed_Reviews: function(row) { return row.reviewStatusData.numCompletedReviews; }
  };

  var sortResults = function(newOption, switchOrder) {
    $(container + ' .form-search').val('');

    if (switchOrder) {
      order = order === 'asc' ? 'desc' : 'asc';
    }
    rowData = _.orderBy(rowData, sortOptions[newOption], order);
    renderTable(container, rowData);
  };

  var searchResults = function(searchText) {
    $(container).data('lastPageNum', 1);
    $(container + ' .form-sort').val('Reviewer');

    // Currently only searching on reviewer name
    var filterFunc = function(row) {
      return row.summary.name.toLowerCase().indexOf(searchText) !== -1;
    };
    var filteredRows = searchText
      ? _.orderBy(_.filter(rowData, filterFunc), sortOptions['Reviewer'], 'asc')
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
      'msg-unsubmitted-reviews': function(row) {
        return row.reviewProgressData.numCompletedReviews < row.reviewProgressData.numPapers;
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
      message: message
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
      var progressHtml = Handlebars.templates.notesReviewerProgress(d.reviewProgressData);
      var statusHtml = Handlebars.templates.notesReviewerStatus(d.reviewStatusData);
      return [number, summaryHtml, progressHtml, statusHtml];
    });

    var $container = $(container);
    var tableData = {
      headings: ['#', 'Reviewer', 'Review Progress', 'Status'],
      rows: rowData,
      extraClasses: 'console-table'
    };
    var pageNum = $container.data('lastPageNum') || 1;
    renderPaginatedTable($container, tableData, pageNum);

    $container.on('click', 'ul.pagination > li > a', function(e) {
      paginationOnClick($(this).parent(), $container, tableData);
      return false;
    });

    $('.message-reviewers-container li > a', container).off('click').on('click', function(e) {
      var filter = $(this).attr('class');
      $('#message-reviewers-modal').remove();

      var defaultBody = '';

      var modalHtml = Handlebars.templates.messageReviewersModalFewerOptions({
        filter: filter,
        defaultSubject: SHORT_PHRASE + ' Reminder',
        defaultBody: defaultBody,
      });
      $('body').append(modalHtml);
      $('#message-reviewers-modal .modal-body > p').text('Enter a message to be sent to all selected reviewers below. You will have a chance to review a list of all recipients after clicking "Next" below.')

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

  displaySortPanel(container, sortOptions, sortResults, searchResults);
  $(container).find('form.search-form .pull-left').html(
    '<div class="btn-group message-reviewers-container" role="group">' +
      '<button type="button" class="message-reviewers-btn btn btn-icon dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
        '<span class="glyphicon glyphicon-envelope"></span> &nbsp;Message Reviewers ' +
        '<span class="caret"></span>' +
      '</button>' +
      '<ul class="dropdown-menu">' +
        (BID_NAME ? '<li><a class="msg-no-bids">Reviewers with 0 bids</a></li>' : '') +
        '<li><a class="msg-unsubmitted-reviews">Reviewers unsubmitted reviews</a></li>' +
      '</ul>' +
    '</div>'
  );
  renderTable(container, rowData);
};

var displayError = function(message) {
  message = message || 'The group data could not be loaded.';
  $('#notes').empty().append('<div class="alert alert-danger"><strong>Error:</strong> ' + message + '</div>');
};

var updateReviewerContainer = function(paperNumber) {
  $addReviewerContainer = $('#' + paperNumber + '-add-reviewer');
  $reviewerProgressContainer = $('#' + paperNumber + '-reviewer-progress');
  var paperForum = $reviewerProgressContainer.data('paperForum');

  var dropdownOptions = conferenceStatusData.reviewerOptions;
  var filterOptions = function(options, term) {
    return _.filter(options, function(p) {
      return _.includes(p.description.toLowerCase(), term.toLowerCase());
    });
  };
  var placeholder = 'reviewer@domain.edu';

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

  $addReviewerContainer.empty().append(
    $dropdown,
    '<button class="btn btn-xs btn-assign-reviewer" data-paper-number=' + paperNumber +
      ' data-paper-forum=' + paperForum + '>Assign</button>'
  );
}


// Helper functions
var paperTableReferrerUrl = encodeURIComponent('[Program Chair Console](/group?id=' + CONFERENCE_ID + '/Program_Chairs#paper-status)');

var buildPaperTableRow = function(note, reviewerIds, completedReviews, metaReview, areachairProfile, decision) {
  // Checkbox for selecting each row
  var cellCheck = { selected: false, noteId: note.id };

  // Build Note Summary Cell
  note.content.authors = null;  // Don't display 'Blinded Authors'
  var cell1 = note;
  cell1.referrer = paperTableReferrerUrl;

  // Build Review Progress Cell
  var reviewObj;
  var combinedObj = {};
  var ratings = [];
  var confidences = [];
  for (var reviewerNum in reviewerIds) {
    var reviewer = reviewerIds[reviewerNum];
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
    expandReviewerList: false,
    enableReviewerReassignment : ENABLE_REVIEWER_REASSIGNMENT,
    referrer: paperTableReferrerUrl
  };
  reviewerSummaryMap[note.number] = reviewProgressData;

  var areachairProgressData = {
    numMetaReview: metaReview ? 'One' : 'No',
    areachair: areachairProfile,
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

var acTableeferrerUrl = encodeURIComponent('[Program Chair Console](/group?id=' + CONFERENCE_ID + '/Program_Chairs#areachair-status)');

var buildSPCTableRow = function(index, areaChair, papers) {

  var summary = {
    id: areaChair.id,
    name: areaChair.name,
    email: areaChair.email,
    showBids: !!BID_NAME,
    completedBids: areaChair.bidCount || 0,
    edgeBrowserBidsUrl: buildEdgeBrowserUrl('tail:' + areaChair.id, AREA_CHAIRS_ID, BID_NAME),
    showRecommendations: !!RECOMMENDATION_NAME,
    completedRecs: areaChair.acRecommendationCount || 0,
    edgeBrowserRecsUrl: buildEdgeBrowserUrl('signatory:' + areaChair.id, REVIEWERS_ID, RECOMMENDATION_NAME)
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

var pcTableReferrerUrl = encodeURIComponent('[Program Chair Console](/group?id=' + CONFERENCE_ID + '/Program_Chairs#reviewer-status)');

var buildPCTableRow = function(index, reviewer, papers) {

  var summary = {
    id: reviewer.id,
    name: reviewer.name,
    email: reviewer.email,
    showBids: !!BID_NAME,
    completedBids: reviewer.bidCount || 0,
    edgeBrowserBidsUrl: buildEdgeBrowserUrl('tail:' + reviewer.id, REVIEWERS_ID, BID_NAME)
  }

  var reviewProgressData = {
    numCompletedMetaReviews: _.filter(papers, function(p) { return p.metaReview; }).length,
    numCompletedReviews: _.filter(papers, function(p) { return p.review; }).length,
    numPapers: papers.length,
    papers: _.sortBy(papers, [function(p) { return p.note.number; }]),
    referrer: pcTableReferrerUrl
  }

  var numCompletedReviews = 0;
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
    }

    if (ratings.length == numOfReviewers) {
      numCompletedReviews++;
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

  var reviewStatusData = {
    numCompletedReviews: numCompletedReviews,
    numPapers: papers.length,
    papers: _.sortBy(paperProgressData, [function(p) { return p.note.number; }]),
    referrer: pcTableReferrerUrl
  }

  return {
    summary: summary,
    reviewProgressData: reviewProgressData,
    reviewStatusData: reviewStatusData
  }
};

// Kick the whole thing off
main();

// Event handlers
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
      '\n\nThank you,\n' + SHORT_PHRASE + ' Program Chair',
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
  var alreadyAssigned = _.find(reviewerSummaryMap[paperNumber].reviewers, function(rev) {
    return (rev.email === userToAdd) || (rev.id === userToAdd);
  });
  if (alreadyAssigned) {
    promptError('Reviewer ' + view.prettyId(userToAdd) + ' has already been assigned to Paper ' + paperNumber.toString());
    return false;
  }
  if (!_.startsWith(userToAdd, '~')) {
    userToAdd = userToAdd.toLowerCase();
  }

  var nextAnonNumber = findNextAnonGroupNumber(paperNumber);
  var reviewerProfile = {
    email : userToAdd,
    id : userToAdd,
    name: '',
    content: {
      names: [{ username: userToAdd }]
    }
  };

  getUserProfiles([userToAdd])
  .then(function(userProfile) {
    if (userProfile && Object.keys(userProfile).length) {
      reviewerProfile = userProfile[Object.keys(userProfile)[0]];
    }
    return Webfield.put('/groups/members', {
      id: CONFERENCE_ID + '/Paper' + paperNumber + '/Reviewers',
      members: [reviewerProfile.id]
    })
  })
  .then(function(result) {
    var commonReaders = [CONFERENCE_ID, CONFERENCE_ID + '/Program_Chairs'];
    if (AREA_CHAIRS_ID) {
      commonReaders.push(CONFERENCE_ID + '/Paper' + paperNumber + '/Area_Chairs');
    }
    return Webfield.post('/groups', {
      id: CONFERENCE_ID + '/Paper' + paperNumber + '/AnonReviewer' + nextAnonNumber,
      members: [reviewerProfile.id],
      readers: commonReaders.concat(CONFERENCE_ID + '/Paper' + paperNumber + '/AnonReviewer' + nextAnonNumber),
      nonreaders: [CONFERENCE_ID + '/Paper' + paperNumber + '/Authors'],
      writers: commonReaders,
      signatures: [CONFERENCE_ID + '/Program_Chairs'],
      signatories: [CONFERENCE_ID + '/Paper' + paperNumber + '/AnonReviewer' + nextAnonNumber]
    })
  })
  .then(function(result) {
    return Webfield.put('/groups/members', {
      id: REVIEWERS_ID,
      members: [reviewerProfile.id]
    })
  })
  .then(function(result) {
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
    reviewerSummaryMap[paperNumber].enableReviewerReassignment = ENABLE_REVIEWER_REASSIGNMENT;
    var $revProgressDiv = $('#' + paperNumber + '-reviewer-progress');
    $revProgressDiv.html(Handlebars.templates.noteReviewers(reviewerSummaryMap[paperNumber]));
    updateReviewerContainer(paperNumber);

    conferenceStatusData.profiles[reviewerProfile.id] = reviewerProfile;
    if (paperNumber in conferenceStatusData.reviewerGroups.byNotes) {
      conferenceStatusData.reviewerGroups.byNotes[paperNumber][nextAnonNumber] = reviewerProfile;
    } else {
      conferenceStatusData.reviewerGroups.byNotes[paperNumber] = { nextAnonNumber : reviewerProfile };
    }
    if (reviewerProfile.id in conferenceStatusData.reviewerGroups.byReviewers) {
      conferenceStatusData.reviewerGroups.byReviewers[reviewerProfile.id].push(paperNumber);
    } else {
      conferenceStatusData.reviewerGroups.byReviewers[reviewerProfile.id] = [paperNumber];
    }
    paperStatusNeedsRerender = true;

    promptMessage('Email has been sent to ' + view.prettyId(reviewerProfile.id) + ' about their new assignment to paper ' + paperNumber, { overlay: true });
    var postData = {
      groups: [reviewerProfile.id],
      subject: SHORT_PHRASE + ': You have been assigned as a Reviewer for paper number ' + paperNumber,
      message: 'This is to inform you that you have been assigned as a Reviewer for paper number ' + paperNumber +
        ' for ' + SHORT_PHRASE + '.' +
        '\n\nTo review this new assignment, please login to OpenReview and go to ' +
        'https://openreview.net/forum?id=' + paperForum + '&invitationId=' + getInvitationId(OFFICIAL_REVIEW_NAME, paperNumber.toString()) +
        '\n\nTo see all of your assigned papers, go to https://openreview.net/group?id=' + REVIEWERS_ID +
        '\n\nThank you,\n' + SHORT_PHRASE + ' Program Chair'
    };
    if (EMAIL_SENDER) {
      postData.from = EMAIL_SENDER;
    }
    return Webfield.post('/messages', postData);
  });
  return false;
});

$('#group-container').on('click', 'a.unassign-reviewer-link', function(e) {
  var $link = $(this);
  var userId = $link.data('userId');
  var paperNumber = $link.data('paperNumber');
  var reviewerNumber = $link.data('reviewerNumber');

  var membersToDelete = [
    reviewerSummaryMap[paperNumber].reviewers[reviewerNumber].id
  ];
  _.forEach(reviewerSummaryMap[paperNumber].reviewers[reviewerNumber].allEmails, function(email){
    membersToDelete.push(email);
  });
  _.forEach(reviewerSummaryMap[paperNumber].reviewers[reviewerNumber].allNames, function(name){
    membersToDelete.push(name);
  });

  Webfield.delete('/groups/members', {
    id: CONFERENCE_ID + '/Paper' + paperNumber + '/Reviewers',
    members: membersToDelete
  })
  .then(function(result) {
    return Webfield.delete('/groups/members', {
      id: CONFERENCE_ID + '/Paper' + paperNumber + '/AnonReviewer' + reviewerNumber,
      members: membersToDelete
    });
  })
  .then(function(result) {

    if (!(conferenceStatusData.reviewerGroups.byReviewers[userId])) {
      // This checks for the case when userId is not the actual group id stored in the reviewers and the anonReviewers groups
      var idInMap = _.find(membersToDelete, function(member){
        return conferenceStatusData.reviewerGroups.byReviewers.hasOwnProperty(member);
      });
      if (idInMap) {
        userId = idInMap;
      } else {
        // This means that the delete calls earlier failed as well
        promptMessage('Sorry, a problem occurred while removing the reviewer ' + view.prettyId(userId) + '. Please contact info@openreview.net.', { overlay: true });
        return false;
      }
    }

    var currentReviewerToPapersMap = conferenceStatusData.reviewerGroups.byReviewers[userId];

    if (currentReviewerToPapersMap.length === 1) {
      delete conferenceStatusData.reviewerGroups.byReviewers[userId];
    } else {
      conferenceStatusData.reviewerGroups.byReviewers[userId] = currentReviewerToPapersMap.filter(function(number) {
        return number !== paperNumber;
      });
    }

    var currentPaperToReviewersMap = conferenceStatusData.reviewerGroups.byNotes[paperNumber];

    if (currentPaperToReviewersMap.length === 1) {
      // The paper has exactly one reviewer, so we delete the paper itself from the map
      delete conferenceStatusData.reviewerGroups.byNotes[paperNumber];
    } else {
      // The paper has more than 1 reviewers, so we just remove the reviewer for this paper
      var reviewerIndex;
      for (key in currentPaperToReviewersMap) {
        if (currentPaperToReviewersMap[key].id === userId) {
          reviewerIndex = key;
          break;
        }
      }
      delete currentPaperToReviewersMap[reviewerIndex];
    }

    var $revProgressDiv = $('#' + paperNumber + '-reviewer-progress');
    delete reviewerSummaryMap[paperNumber].reviewers[reviewerNumber];
    reviewerSummaryMap[paperNumber].numReviewers = reviewerSummaryMap[paperNumber].numReviewers ? reviewerSummaryMap[paperNumber].numReviewers - 1 : 0;
    reviewerSummaryMap[paperNumber].expandReviewerList = true;
    $revProgressDiv.html(Handlebars.templates.noteReviewers(reviewerSummaryMap[paperNumber]));
    updateReviewerContainer(paperNumber);
    promptMessage('Reviewer ' + view.prettyId(userId) + ' has been removed for paper ' + paperNumber, { overlay: true });
    paperStatusNeedsRerender = true;
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
  } else if (containerId === '#reviewer-status') {
    displayReviewerStatusTable();
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
