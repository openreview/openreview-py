// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Author Console Webfield
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var BLIND_SUBMISSION_ID = '';
var OFFICIAL_REVIEW_NAME = '';
var DECISION_NAME = '';
var REVIEW_RATING_NAME = 'rating';
var REVIEW_CONFIDENCE_NAME = 'confidence';
var HEADER = {};
var AUTHOR_NAME = 'Authors';
var AUTHOR_SUBMISSION_FIELD = '';
var PAPER_RANKING_ID = CONFERENCE_ID + '/' + AUTHOR_NAME + '/-/Paper_Ranking';
var WILDCARD_INVITATION = CONFERENCE_ID + '.*';

function main() {
  // In the future this should not be necessary as the group's readers
  // will prevent unauthenticated users
  if (!user || !user.profile || user.profile.id === 'guest') {
    location.href = '/login?redirect=' + encodeURIComponent(
      location.pathname + location.search + location.hash
    );
    return;
  }

  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  renderHeader();

  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID);
  }

  load().then(renderContent).then(Webfield.ui.done);
}

// Load makes all the API calls needed to get the data to render the page
function load() {
  var query = {
    invitation: SUBMISSION_ID,
    details: 'invitation,overwriting,directReplies',
    sort: 'number:asc'
  }
  query[AUTHOR_SUBMISSION_FIELD] = user.profile.id;
  var notesP = Webfield.get('/notes', query).then(function(result) {
    //Get the blind submissions to have backward compatibility with the paper number
    var originalNotes = result.notes;
    blindNoteIds = [];
    originalNotes.forEach(function(note) {
      if (note.details.overwriting && note.details.overwriting.length) {
        blindNoteIds.push(note.details.overwriting[0]);
      }
    });

    if (blindNoteIds.length) {
      return Webfield.get('/notes', {
        ids: blindNoteIds,
        details: 'directReplies',
        sort: 'number:asc'
      })
      .then(function(result) {
        return (result.notes || []).filter(function(note) {
          return note.invitation === BLIND_SUBMISSION_ID;
        }).map(function(blindNote) {
          var originalNote = originalNotes.find(function(o) { return o.id == blindNote.original;});
          blindNote.content.authors = originalNote.content.authors;
          blindNote.content.authorids = originalNote.content.authorids;
          return blindNote;
        });
      });
    } else {
      return result.notes;
    }
  });

  return $.when(notesP, getAllInvitations());
}

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
    return _.some(inv.invitees, function(invitee) { return invitee.indexOf(AUTHOR_NAME) !== -1; });
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


// Render functions
function renderHeader() {
  Webfield.ui.header(HEADER.title, HEADER.instructions);

  var loadingMessage = '<p class="empty-message">Loading...</p>';
  var sections = [
    {
      heading: 'Your Submissions',
      id: 'your-submissions',
      content: loadingMessage,
      extraClasses: 'horizontal-scroll',
      active: true
    },
    {
      heading: 'Author Tasks',
      id: 'author-tasks',
      content: loadingMessage
    }
  ];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: false
  });
}

function renderContent(authorNotes, invitations) {
  // Author Tasks tab
  var tasksOptions = {
    container: '#author-tasks',
    emptyMessage: 'No outstanding tasks for this conference',
    referrer: encodeURIComponent('[Author Console](/group?id=' + CONFERENCE_ID + '/' + AUTHOR_NAME + '#author-tasks)') + '&t=' + Date.now()
  };
  $(tasksOptions.container).empty();

  // Render table like AC console
  renderStatusTable(authorNotes);

  // Add paper ranking tag widgets to the table of submissions
  // If tag invitation does not exist, get existing tags and display read-only
  var paperRankingInvitation = _.find(invitations, ['id', PAPER_RANKING_ID]);
  if (paperRankingInvitation) {
    var paperRankingTags = paperRankingInvitation.details.repliedTags || [];
    displayPaperRanking(authorNotes, paperRankingInvitation, paperRankingTags);
  } else {
    Webfield.get('/tags', { invitation: PAPER_RANKING_ID })
      .then(function(result) {
        if (!result.tags || !result.tags.length) {
          return;
        }
        displayPaperRanking(authorNotes, null, result.tags);
      });
  }

  Webfield.ui.newTaskList(invitations, [], tasksOptions);

  // Remove spinner and show content
  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

function renderStatusTable(notes) {
  var $container = $('#your-submissions');
  var rows = notes.map(function(note) {
    var invitationPrefix = CONFERENCE_ID + '/Paper' + note.number + '/-/';
    var decision = _.find(note.details.directReplies, ['invitation', invitationPrefix + DECISION_NAME]);
    var noteCompletedReviews = _.filter(note.details.directReplies, ['invitation', invitationPrefix + OFFICIAL_REVIEW_NAME]);

    return buildTableRow(note, noteCompletedReviews, decision);
  });

  if (rows.length === 0) {
    $container.empty().append('<p class="empty-message">No papers to display at this time</p>');
    return;
  }

  var templateFuncs = [
    function(data) {
      return '<strong class="note-number">' + data.number + '</strong>';
    },
    Handlebars.templates.noteSummary,
    renderReviewSummary,
    Handlebars.templates.noteMetaReviewStatus
  ];
  var rowsHtml = rows.map(function(row) {
    return row.map(function(cell, i) {
      return templateFuncs[i](cell);
    });
  });

  var tableHtml = Handlebars.templates['components/table']({
    headings: ['#', 'Paper Summary', 'Reviews', 'Decision'],
    rows: rowsHtml,
    extraClasses: 'console-table'
  });

  $container.empty().append(tableHtml);

  $('#your-submissions .console-table th').eq(0).css('width', '5%');
  $('#your-submissions .console-table th').eq(1).css('width', '35%');
  $('#your-submissions .console-table th').eq(2).css('width', '30%');
  $('#your-submissions .console-table th').eq(3).css('width', '30%');
}

function buildTableRow(note, completedReviews, decision) {
  // Paper number cell
  var cell0 = { number: note.number };

  // Note summary cell
  var referrerUrl = encodeURIComponent('[Author Console](/group?id=' + CONFERENCE_ID + '/' + AUTHOR_NAME + '#your-submissions)');
  var cell1 = note;
  cell1.referrer = referrerUrl;

  // Review progress cell
  var ratings = [];
  var confidences = [];
  var reviewsFormatted = [];
  completedReviews.forEach(function(review) {
    var reviewFormatted = Object.assign({ id: review.id, forum: note.id }, review.content);
    reviewFormatted.signature = view.prettyId(_.last(review.signatures[0].split('/')))
    reviewFormatted.referrer = referrerUrl;

    // Need to parse rating and confidence strings into ints
    var ratingExp = /^(\d+): .*$/;
    var ratingMatch = review.content[REVIEW_RATING_NAME] && review.content[REVIEW_RATING_NAME].match(ratingExp);
    var rating = ratingMatch ? parseInt(ratingMatch[1], 10) : null;
    if (rating) {
      ratings.push(rating);
      reviewFormatted.rating = rating;
    }
    var confidenceMatch = review.content[REVIEW_CONFIDENCE_NAME] && review.content[REVIEW_CONFIDENCE_NAME].match(ratingExp);
    var confidence = confidenceMatch ? parseInt(confidenceMatch[1], 10) : null;
    if (confidence) {
      confidences.push(confidence);
      reviewFormatted.confidence = confidence;
    }
    reviewsFormatted.push(reviewFormatted);
  });

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
    reviews: reviewsFormatted,
    averageRating: averageRating,
    maxRating: maxRating,
    minRating: minRating,
    averageConfidence: averageConfidence,
    minConfidence: minConfidence,
    maxConfidence: maxConfidence,
  };

  // Status cell
  var cell3 = {};
  if (decision) {
    cell3.recommendation = decision.content.decision;
    cell3.editUrl = '/forum?id=' + note.forum + '&noteId=' + decision.id;
  }

  return [cell0, cell1, cell2, cell3];
}

function renderReviewSummary(data) {
  var reviews = data.reviews || [];
  var reviewList = reviews.map(function(review) {
    return '<li style="margin-bottom: .25rem;"><strong>' + review.signature + ':</strong> Rating: ' + review.rating +
      (review.confidence ? ' / Confidence: ' + review.confidence : '') +
      '<br><a href="/forum?id=' + review.forum + '&noteId=' + review.id + '&referrer=' + review.referrer + '">Read Review</a>' +
      '</li>';
  });
  return '<div class="reviewer-progress">' +
    '<h4>' + reviews.length + ' Reviews Submitted</h4>' +
    '<ul class="list-unstyled" style="font-size: .75rem">' + reviewList.join('\n') + '</ul>' +
    '<div>' +
    (data.averageRating ? '<strong>Average Rating:</strong> ' + data.averageRating + ' (Min: ' + data.minRating + ', Max: ' + data.maxRating + ')' : '') +
    (data.averageConfidence ? '<br><strong>Average Confidence:</strong> ' + data.averageConfidence + ' (Min: ' + data.minConfidence + ', Max: ' + data.maxConfidence + ')' : '') +
    '</div>' +
    '</div>';
}

var displayPaperRanking = function(notes, paperRankingInvitation, paperRankingTags) {
  var invitation = paperRankingInvitation ? _.cloneDeep(paperRankingInvitation) : null;
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
  if (invitation) {
    invitation.reply.content.tag['value-dropdown'] = _.difference(availableOptions, currentRankings);
  }
  var invitationId = invitation ? invitation.id : PAPER_RANKING_ID;

  notes.forEach(function(note, i) {
    $reviewStatusContainer = $('#notes .console-table tbody > tr:nth-child('+ (i + 1) +') > td:nth-child(2)');
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
            signatures: [user.profile.id],
            readers: [CONFERENCE_ID, user.profile.id],
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
              displayPaperRanking(notes, paperRankingInvitation, validTags);
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


// Go!
main();
