// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Lite Author Console Webfield
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var BLIND_SUBMISSION_ID = '';
var OFFICIAL_REVIEW_NAME = '';
var OFFICIAL_META_REVIEW_NAME = '';
var REVIEW_RATING_NAME = 'rating';
var REVIEW_CONFIDENCE_NAME = 'confidence';
var HEADER = {};
var AUTHOR_NAME = 'Authors';
var PAPER_RANKING_ID = CONFERENCE_ID + '/' + AUTHOR_NAME + '/-/Paper_Ranking';
var WILDCARD_INVITATION = CONFERENCE_ID + '.*';

function main() {
  // In the future this should not be necessary as the group's readers
  // will prevent unauthenticated users
  if (!user || !user.profile) {
    location.href = '/login?redirect=' + encodeURIComponent(
      location.pathname + location.search + location.hash
    );
    return;
  }

  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID);
  }

  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  renderHeader();

  load().then(renderContent).then(Webfield.ui.done);
}

// API functions
function load() {
  return Webfield.get('/notes', {
    'content.authorids': user.profile.id,
    invitation: SUBMISSION_ID,
    details: 'overwriting',
    sort: 'number:asc'
  }).then(function(result) {
    // Get the blind submissions to have backward compatibility with the paper number
    var originalNotes = result.notes;
    blindNoteIds = [];
    originalNotes.forEach(function(note) {
      if (note.details.overwriting && note.details.overwriting.length) {
        blindNoteIds.push(note.details.overwriting[0]);
      }
    });

    if (blindNoteIds.length) {
      return Webfield.get('/notes', { ids: blindNoteIds, sort: 'number:asc' })
        .then(function(result) {
          return (result.notes || []).filter(function(note) {
            return note.invitation === BLIND_SUBMISSION_ID;
          }).map(function(blindNote) {
            var originalNote = originalNotes.find(function(o) {
              return o.id === blindNote.original;
            });
            blindNote.content.authors = originalNote.content.authors;
            blindNote.content.authorids = originalNote.content.authorids;
            return blindNote;
          });
        });
    } else {
      return result.notes;
    }
  });
}


// Render functions
function renderHeader() {
  Webfield.ui.header(HEADER.title, HEADER.instructions);

  var sections = [{
    heading: 'Your Submissions',
    id: 'your-submissions',
    content: '<p class="empty-message">Loading...</p>',
    extraClasses: 'horizontal-scroll',
    active: true
  }];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: false
  });
}

function renderContent(authorNotes) {
  // Render table like AC console
  renderStatusTable(authorNotes);

  // Remove spinner and show content
  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

function renderStatusTable(notes) {
  var $container = $('#your-submissions');

  var rows = notes.map(function(note) {
    var metaReview = null;
    var noteCompletedReviews = []
    return buildTableRow(note, noteCompletedReviews, metaReview);
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
    headings: ['#', 'Paper Summary', 'Reviews'].concat(OFFICIAL_META_REVIEW_NAME ? 'Meta Review' : []),
    rows: rowsHtml,
    extraClasses: 'console-table'
  });

  $container.empty().append(tableHtml);

  $('#your-submissions .console-table th').eq(0).css('width', '4%');
  if (OFFICIAL_META_REVIEW_NAME) {
    $('#your-submissions .console-table th').eq(1).css('width', '36%');
    $('#your-submissions .console-table th').eq(2).css('width', '30%');
    $('#your-submissions .console-table th').eq(3).css('width', '30%');
  } else {
    $('#your-submissions .console-table th').eq(1).css('width', '46%');
    $('#your-submissions .console-table th').eq(2).css('width', '50%');
  }
}

function buildTableRow(note, completedReviews, metaReview) {
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
  if (metaReview) {
    cell3.recommendation = metaReview.content.recommendation;
    cell3.editUrl = '/forum?id=' + note.forum + '&noteId=' + metaReview.id;
  }

  return [cell0, cell1, cell2].concat(OFFICIAL_META_REVIEW_NAME ? cell3 : []);
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

// Go!
main();
