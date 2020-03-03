// ------------------------------------
// Author Console Webfield
//
// This webfield displays the conference header (#header), the submit button (#invitation),
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var HEADER = {};
var AUTHOR_NAME = 'Authors';

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showActionButtons: true,
  showContents: true
};


// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  Webfield.ui.header(HEADER.title, HEADER.instructions);
  $('#header').css('margin-bottom', '2rem');

  renderConferenceTabs();

  load().then(renderContent).then(Webfield.ui.done);

  OpenBanner.venueHomepageLink(CONFERENCE_ID);
}


// Load makes all the API calls needed to get the data to render the page
// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/
function load() {

  var authorNotesP;
  var invitationsP;
  var edgeInvitationsP;

  if (!user || _.startsWith(user.id, 'guest_')) {
    authorNotesP = $.Deferred().resolve([]);
    invitationsP = $.Deferred().resolve([]);
    edgeInvitationsP = $.Deferred().resolve([]);

  } else {
    authorNotesP = Webfield.get('/notes', {
      'content.authorids': user.profile.id,
      invitation: SUBMISSION_ID,
      details: 'overwriting'
    }).then(function(result) {
      //Get the blind submissions to have backward compatibility with the paper number
      var originalNotes = result.notes;
      blindNoteIds = [];
      originalNotes.forEach(function(note) {
        if (note.details.overwriting && note.details.overwriting.length) {
          blindNoteIds.push(note.details.overwriting[0]);
        }
      });

      if (blindNoteIds.length) {
        return Webfield.post('/notes/search', {
          ids: blindNoteIds
        })
        .then(function(result) {
          return result.notes.map(function(blindNote) {
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

    invitationsP = Webfield.get('/invitations', {
      regex: CONFERENCE_ID + '.*',
      invitee: true,
      duedate: true,
      replyto: true,
      type: 'notes',
      details:'replytoNote,repliedNotes'
    }).then(function(result) {
      return result.invitations;
    });

    edgeInvitationsP = Webfield.get('/invitations', {
      regex: CONFERENCE_ID + '.*',
      invitee: true,
      duedate: true,
      type: 'edges'
    }).then(function(result) {
      return result.invitations;
    });
  }

  return $.when(authorNotesP, invitationsP, edgeInvitationsP);
}


// Render functions
function renderConferenceTabs() {
  var sections = [
    {
      heading: 'Your Submissions',
      id: 'your-submissions',
      active: true
    },
    {
      heading: 'Author Schedule',
      id: 'author-schedule',
      content: HEADER.schedule
    },
    {
      heading: 'Author Tasks',
      id: 'author-tasks'
    }
  ];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });
}


function renderContent(authorNotes, invitations, edgeInvitations) {
  // Author Tasks tab
  var tasksOptions = {
    container: '#author-tasks',
    emptyMessage: 'No outstanding tasks for this conference',
    referrer: encodeURIComponent('[Author Console](/group?id=' + CONFERENCE_ID + '/' + AUTHOR_NAME + '#author-tasks)')
  }
  $(tasksOptions.container).empty();

  Webfield.ui.newTaskList(invitations, edgeInvitations, tasksOptions);

  //Render table like AC console
  renderStatusTable(authorNotes, {}, [], {}, '#your-submissions');

  $('.console-table th').eq(0).css('width', '4%');
  $('.console-table th').eq(1).css('width', '40%');
  $('.console-table th').eq(2).css('width', '28%');
  $('.console-table th').eq(3).css('width', '28%');

  // Remove spinner and show content
  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}


var renderStatusTable = function(notes, completedReviews, metaReviews, reviewerIds, container) {
  var rows = _.map(notes, function(note) {
    var revIds = reviewerIds[note.number] || Object.create(null);
    var metaReview = _.find(metaReviews, ['invitation', 'replace_invitation_id']);
    var noteCompletedReviews = completedReviews[note.number] || Object.create(null);

    return buildTableRow(note, revIds, noteCompletedReviews, metaReview);
  });

  if (rows.length) {
    renderTableRows(rows, container);
  } else {
    $(container).empty().append('<p class="empty-message">No papers to display at this time</p>');
  }
};

var renderTableRows = function(rows, container) {
  var templateFuncs = [
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
      'Paper ID', 'Paper Summary'
      // Temporally hide review status
      //, 'Review Progress', 'Meta Review Status'
    ],
    rows: rowsHtml,
    extraClasses: 'console-table'
  });

  $('.table-container', container).remove();
  $(container).append(tableHtml);
};

var buildTableRow = function(note, reviewerIds, completedReviews, metaReview) {
  var cellCheck = { selected: false, noteId: note.id };

  // Paper number cell
  var cell0 = { number: note.number};

  // Note summary cell
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
        noteId: note.id
      });
      combinedObj[reviewerNum] = {
        id: reviewer.id,
        name: reviewer.name,
        email: reviewer.email,
        forum: note.forum,
        forumUrl: forumUrl,
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
    numSubmittedReviews: Object.keys(completedReviews).length,
    numReviewers: Object.keys(reviewerIds).length,
    reviewers: combinedObj,
    averageRating: averageRating,
    maxRating: maxRating,
    minRating: minRating,
    averageConfidence: averageConfidence,
    minConfidence: minConfidence,
    maxConfidence: maxConfidence,
    sendReminder: false,
    expandReviewerList: false,
    enableReviewerReassignment : false
  };

  // Status cell
  var cell3 = {};
  if (metaReview) {
    cell3.recommendation = metaReview.content.recommendation;
    cell3.editUrl = '/forum?id=' + note.forum + '&noteId=' + metaReview.id;
  }

  // Temporally hide review status
  //return [cell0, cell1, cell2, cell3];
  return [cell0, cell1];
};

// Go!
main();
