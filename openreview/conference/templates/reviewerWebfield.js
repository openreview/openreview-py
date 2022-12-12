// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var BLIND_SUBMISSION_ID = '';
var HEADER = {};
var REVIEWER_NAME = '';
var AREACHAIR_NAME = '';
var OFFICIAL_REVIEW_NAME = '';
var REVIEW_RATING_NAME = 'rating';
var LEGACY_INVITATION_ID = false;
var REVIEW_LOAD = '';
var CUSTOM_LOAD_INVITATION = '';

var WILDCARD_INVITATION = CONFERENCE_ID + '/.*';
var PAPER_RANKING_ID = CONFERENCE_ID + '/' + REVIEWER_NAME + '/-/Paper_Ranking';
var CUSTOM_MAX_PAPERS_ID = CONFERENCE_ID + '/' + REVIEWER_NAME + '/-/Custom_Max_Papers';

var main = function() {
  // In the future this should not be necessary as the group's readers
  // will prevent unauthenticated users
  if (!user || !user.profile) {
    location.href = '/login?redirect=' + encodeURIComponent(
      location.pathname + location.search + location.hash
    );
    return;
  }

  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID);
  }

  displayHeader();

  loadReviewerData()
    .then(function(
      blindedNotes, officialReviews, invitations, customLoad, groupByNumber, areaChairMap
    ) {
      if (customLoad) {
        $('#header .description').append(
          '<p class="dark">You have agreed to review up to <strong>' + customLoad + ' papers</strong>.</p>'
        );
      }

      displayStatusTable(blindedNotes, officialReviews, invitations);

      // Add AC information to table
      if (!_.isEmpty(areaChairMap)) {
        $('.console-table div.note').each(function() {
          var num = $(this).attr('id').split('-').pop();
          $(this).append(
            '<div class="note-area-chairs">' +
              '<p><strong>Area Chair:</strong> ' +
              '<a href="https://openreview.net/profile?id=' + areaChairMap[num] + '" target="_blank">' + view.prettyId(areaChairMap[num]) + ' </a></p>' +
            '</div>'
          );
        });
      }

      // Add AC information to table
      if (areaChairMap) {
        $('.console-table div.note').each(function() {
          var noteId = $(this).data('id');
          $(this).find('.note-content').before(
            '<div class="note-area-chairs">' +
              '<h4>Assigned Area Chair:</h4>' +
              '<p><a href="https://openreview.net/profile?id=' + areaChairMap[noteId] + '" target="_blank">' + view.prettyId(areaChairMap[noteId]) + ' </a></p>' +
            '</div>'
          );
        });
      }

      // Add paper ranking tag widgets to the table of submissions
      // If tag invitation does not exist, get existing tags and display read-only
      var paperRankingInvitation = _.find(invitations, ['id', PAPER_RANKING_ID]);
      if (paperRankingInvitation) {
        var paperRankingTags = paperRankingInvitation.details.repliedTags || [];
        displayPaperRanking(blindedNotes, paperRankingInvitation, paperRankingTags, groupByNumber);
      } else {
        Webfield.get('/tags', { invitation: PAPER_RANKING_ID })
          .then(function(result) {
            if (!result.tags || !result.tags.length) {
              return;
            }
            displayPaperRanking(blindedNotes, null, result.tags, groupByNumber);
          });
      }

      displayTasks(invitations);
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
  var singularName = REVIEWER_NAME.endsWith('s') ? REVIEWER_NAME.slice(0, -1) : REVIEWER_NAME;
  return Webfield.getAll('/groups', {
    regex: WILDCARD_INVITATION,
    member: user.id
  }).then(function(groups) {

    var anonGroups = _.filter(groups, function(g) { return g.id.includes('/' + singularName + '_'); });
    var reviewerGroups = _.filter(groups, function(g) { return g.id.endsWith('/' + REVIEWER_NAME); });

    var groupByNumber = {};
    _.forEach(reviewerGroups, function(reviewerGroup) {
      var num = getNumberFromGroup(reviewerGroup.id, 'Paper');
      var anonGroup = anonGroups.find(function(anonGroup) { return anonGroup.id.startsWith(CONFERENCE_ID + '/Paper' + num + '/' + singularName + '_'); });
      if (anonGroup) {
        groupByNumber[num] = anonGroup.id;
      }
    });

    return groupByNumber;

  });
};

var getAreaChairGroups = function(noteNumbers) {
  var ids = _.map(noteNumbers, function(noteNumber) {
    return CONFERENCE_ID + '/Paper' + noteNumber + '/Area_Chairs';
  });
  
  if (!ids.length) {
    return $.Deferred().resolve({});
  }

  var allAreaChairGroupsP = Webfield.getAll('/groups', {
    ids: ids,
    select: 'id,members'
  })
  .then(function(groups) {

    var groupByNumber = {};
    _.forEach(groups, function(group) {
      var num = getNumberFromGroup(group.id, 'Paper');
      groupByNumber[num] = group.members[0];
    });

    return groupByNumber;
  });

  return $.when(allAreaChairGroupsP);
};

var getBlindedNotes = function(noteNumbers) {
  if (!noteNumbers || !noteNumbers.length) {
    return $.Deferred().resolve([]);
  }

  return Webfield.get('/notes', {
    invitation: BLIND_SUBMISSION_ID,
    number: noteNumbers.join(','),
    select: 'id,number,forum,content.title,content.authors,content.authorDomains,content.pdf',
    details: 'invitation',
    sort: 'number:asc'
  }).then(function(result) {
    return result.notes || [];
  });
};

var getOfficialReviews = function(noteNumbers) {
  if (!noteNumbers || !noteNumbers.length) {
    return $.Deferred().resolve([]);
  }

  var promises = _.map(noteNumbers, function(noteNumber) {
    return Webfield.get('/notes', {
      invitation: getInvitationId(OFFICIAL_REVIEW_NAME, noteNumber),
      tauthor: true
    }).then(function(result) {
      return result.notes || [];
    });
  });

  return $.when.apply($, promises).then(function() {
    return _.flatten(_.values(arguments));
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
    return _.some(inv.invitees, function(invitee) { return invitee.indexOf(REVIEWER_NAME) !== -1; });
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

var getCustomLoad = function(userIds) {
  return Webfield.get('/edges', { invitation: CUSTOM_MAX_PAPERS_ID, tail: user.id })
    .then(function(result) {
      if (result.edges && result.edges.length) {
        return result.edges[0].weight;
      }
      return Webfield.get('/notes', { invitation: CUSTOM_LOAD_INVITATION, select: 'content.reviewer_load,content.user,content.reduced_load' })
      .then(function(result) {
        if (!result.notes || !result.notes.length) {
          return REVIEW_LOAD;
        }
        if (result.notes.length === 1) {
          return result.notes[0].content.reviewer_load || result.notes[0].content.reduced_load;
        } else {
          // If there is more than one there might be a Program Chair
          var loads = result.notes.filter(function(note) {
            return userIds.indexOf(note.content.user) > -1;
          });
          return loads.length ? (loads[0].content.reviewer_load || loads[0].content.reduced_load ) : REVIEW_LOAD;
        }
      });
    })

};

var loadReviewerData = function() {
  var userIds = _.union(user.profile.usernames, user.profile.emails);

  return getReviewerNoteNumbers()
    .then(function(groupByNumber) {
      var noteNumbers = Object.keys(groupByNumber);
      return $.when(
        getBlindedNotes(noteNumbers),
        getOfficialReviews(noteNumbers),
        getAllInvitations(),
        getCustomLoad(userIds),
        groupByNumber,
        getAreaChairGroups(noteNumbers)
      );
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

var displayStatusTable = function(notes, officialReviews, invitations) {
  var $container = $('#assigned-papers');

  if (notes.length === 0) {
    $container.empty().append(
      '<p class="empty-message">You have no assigned papers. Please check again after the paper assignment process is complete.</p>'
    );
    return;
  }

  var rowData = notes.map(function(note) {
    var invId = getInvitationId(OFFICIAL_REVIEW_NAME, note.number);
    var officialReview = _.find(officialReviews, ['invitation', invId]);
    var officialReviewInvitation = _.find(invitations, ['id', invId]);
    return buildTableRow(note, officialReview, officialReviewInvitation);
  });

  var tableHTML = Handlebars.templates['components/table']({
    headings: ['#', 'Paper Summary', 'Your Ratings'],
    rows: rowData,
    extraClasses: 'console-table'
  });

  $container.empty().append(tableHTML);
};

var buildTableRow = function(note, officialReview, officialReviewInvitation) {
  var referrerUrl = encodeURIComponent('[Reviewer Console](/group?id=' + CONFERENCE_ID + '/' + REVIEWER_NAME + '#assigned-papers)');
  var number = '<strong class="note-number">' + note.number + '</strong>';

  // Note Summary Cell
  var cell1 = note;
  cell1.content.authors = null;  // Don't display 'Blinded Authors'
  cell1.referrer = referrerUrl;
  var summaryHtml = Handlebars.templates.noteSummary(cell1);

  // Status Cell
  var reviewStatus = officialReviewInvitation ? {
    invitationUrl: '/forum?id=' + note.forum + '&noteId=' + note.forum + '&invitationId=' + officialReviewInvitation.id + '&referrer=' + referrerUrl,
    invitationName: 'Official Review'
  } : {};
  if (officialReview) {
    reviewStatus.paperRating = officialReview.content[REVIEW_RATING_NAME];
    reviewStatus.review = officialReview.content.review;
    reviewStatus.editUrl = '/forum?id=' + note.forum + '&noteId=' + officialReview.id + '&referrer=' + referrerUrl;
  }
  var statusHtml = Handlebars.templates.noteReviewStatus(reviewStatus);

  return [number, summaryHtml, statusHtml];
};

var displayPaperRanking = function(notes, paperRankingInvitation, paperRankingTags, groupByNumber) {
  var invitation = paperRankingInvitation ? _.cloneDeep(paperRankingInvitation) : null;
  if (invitation) {
    var availableOptions = ['No Ranking'];
    var validTags = [];
    notes.forEach(function(note, index) {
      availableOptions.push((index + 1) + ' of ' + notes.length );
      noteTags = paperRankingTags.filter(function(tag) { return tag.forum === note.forum; })
      if (noteTags.length) {
        validTags.push(noteTags[0]);
      }
    })
    var currentRankings = validTags.map(function(tag) {
      if (!tag.tag || tag.tag === 'No Ranking') {
        return null;
      }
      return tag.tag;
    });
    invitation.reply.content.tag['value-dropdown'] = _.difference(availableOptions, currentRankings);
  }
  var invitationId = invitation ? invitation.id : PAPER_RANKING_ID;

  notes.forEach(function(note, i) {
    $reviewStatusContainer = $('#assigned-papers .console-table tbody > tr:nth-child('+ (i + 1) +') > td:nth-child(3)');
    if (!$reviewStatusContainer.length) {
      return;
    }

    var index = _.findIndex(validTags, ['forum', note.forum]);
    var $tagWidget = view.mkTagInput(
      'tag',
      invitation && invitation.reply.content.tag,
      index !== -1 ? [validTags[index]] : [],
      {
        forum: note.id,
        placeholder: (invitation && invitation.reply.content.tag.description) || view.prettyInvitationId(invitationId),
        label: view.prettyInvitationId(invitationId),
        readOnly: false,
        onChange: function(id, value, deleted, done) {
          var body = {
            id: id,
            tag: value,
            signatures: [groupByNumber[note.number]],
            readers: [CONFERENCE_ID, CONFERENCE_ID + '/Paper' + note.number + '/' + AREACHAIR_NAME, groupByNumber[note.number]],
            forum: note.id,
            invitation: invitationId,
            ddate: deleted ? Date.now() : null
          };
          $('.tag-widget button').attr('disabled', true);
          Webfield.post('/tags', body)
            .then(function(result) {
              if (index !== -1) {
                validTags.splice(index, 1, result);
              } else {
                validTags.push(result);
              }
              displayPaperRanking(notes, paperRankingInvitation, validTags, groupByNumber);
              done(result);
            })
            .fail(function(error) {
              promptError(error ? error : 'The specified tag could not be updated');
            });
        }
      }
    );
    $reviewStatusContainer.find('.tag-widget').remove();
    $reviewStatusContainer.append($tagWidget);
  });
};

var displayTasks = function(invitations) {
  //  My Tasks tab
  var tasksOptions = {
    container: '#reviewer-tasks',
    emptyMessage: 'You have no outstanding tasks for this conference.',
    referrer: encodeURIComponent('[Reviewer Console](/group?id=' + CONFERENCE_ID + '/' + REVIEWER_NAME + '#reviewer-tasks)')
  }
  $(tasksOptions.container).empty();

  Webfield.ui.newTaskList(invitations, [], tasksOptions)
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
