// ------------------------------------
// Venue homepage template
//
// This webfield displays the conference header (#header), the submit button (#invitation),
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var CONFERENCE_ID = '.TMLR';
var SUBMISSION_ID = '.TMLR/-/Author_Submission';
var SUBMITTED_ID = '.TMLR/Submitted';
var UNDER_REVIEW_ID = '.TMLR/Under_Review';
var DESK_REJECTED_ID = '.TMLR/Desk_Rejection';
var HEADER = {};

var WILDCARD_INVITATION = CONFERENCE_ID + '/.*';
var PAGE_SIZE = 50;

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true,
  showTags: false,
  referrer: encodeURIComponent('[TMLR](/group?id=' + CONFERENCE_ID + '#submissions)')
};
var commentDisplayOptions = {
  pdfLink: false,
  replyCount: true,
  showContents: false,
  showParent: true
};

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  renderConferenceHeader();

  renderSubmissionButton();

  renderConferenceTabs();

  load().then(renderContent).then(Webfield.ui.done);
}

// Load makes all the API calls needed to get the data to render the page
// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/
function load() {

  var submittedNotesP = Webfield.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': SUBMITTED_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var underReviewNotesP = Webfield.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': UNDER_REVIEW_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var deskRejectedNotesP = Webfield.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': DESK_REJECTED_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var activityNotesP = $.Deferred().resolve([]);
  if (user && !_.startsWith(user.id, 'guest_')) {
    activityNotesP = Webfield.api.getSubmissions(WILDCARD_INVITATION, {
      pageSize: PAGE_SIZE,
      details: 'forumContent,writable'
    });
  }

  return $.when(submittedNotesP, underReviewNotesP, deskRejectedNotesP, activityNotesP);
}

// Render functions
function renderConferenceHeader() {
  Webfield.ui.venueHeader(HEADER);

  Webfield.ui.spinner('#notes', { inline: true });
}

function renderSubmissionButton() {
  Webfield.api.getSubmissionInvitation(SUBMISSION_ID)
    .then(function(invitation) {
      Webfield.ui.submissionButton(invitation, user, {
        onNoteCreated: function() {
          // Callback funtion to be run when a paper has successfully been submitted (required)
          promptMessage('Your submission is complete. Check your inbox for a confirmation email. ');

          load().then(renderContent).then(function() {
            $('.tabs-container a[href="#your-consoles"]').click();
          });
        }
      });
    });
}

function renderConferenceTabs() {

  var sections = [
  {
    heading: 'Under Review',
    id: 'under-review-submissions',
  },
  {
    heading: 'Submissions',
    id: 'submissions',
  },
  {
    heading: 'Desk Rejected Submissions',
    id: 'desk-rejected-submissions',
  },
  {
    heading: 'Recent Activity',
    id: 'recent-activity',
  }];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });
}

function renderContent(submittedResponse, underReviewResponse, deskRejectedResponse, activityNotes) {

  var underReviewSubmissions = underReviewResponse.notes || [];
  var underReviewCount = underReviewResponse.count || 0;

  $('#under-review-submissions').empty();

  if (underReviewCount) {
    var searchResultsListOptions = _.assign({}, paperDisplayOptions, {
      container: '#under-review-submissions',
      autoLoad: false
    });

    Webfield.ui.submissionList(underReviewSubmissions, {
      heading: null,
      container: '#under-review-submissions',
      search: {
        enabled: true,
        localSearch: false,
        invitation: SUBMISSION_ID,
        onResults: function(searchResults) {
          Webfield.ui.searchResults(searchResults, searchResultsListOptions);
        },
        onReset: function() {
          Webfield.ui.searchResults(notes, searchResultsListOptions);
          $('#under-review-submissions').append(view.paginationLinks(underReviewCount, PAGE_SIZE, 1));
        }
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: underReviewCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': UNDER_REVIEW_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#submissions"]').parent().hide();
  }

  var submissionNotesCount = submittedResponse.count || 0;
  if (submissionNotesCount) {
    $('#submissions').empty();

    var notes = submittedResponse.notes || [];
    Webfield.ui.submissionList(notes, {
      heading: null,
      container: '#submissions',
      search: {
        enabled: false
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: submissionNotesCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': SUBMITTED_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#submissions"]').parent().hide();
  }

  var deskRejectedNotesCount = deskRejectedResponse.count || 0;
  if (deskRejectedNotesCount) {
    $('#desk-rejected-submissions').empty();

    var deskRejectedNotesArray = deskRejectedResponse.notes || [];
    Webfield.ui.submissionList(deskRejectedNotesArray, {
      heading: null,
      container: '#desk-rejected-submissions',
      search: {
        enabled: false
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: deskRejectedNotesCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': DESK_REJECTED_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#desk-rejected-submissions"]').parent().hide();
  }

  // Activity Tab
  if (activityNotes.length) {
    var displayOptions = {
      container: '#recent-activity',
      user: user && user.profile,
      showActionButtons: true
    };

    $(displayOptions.container).empty();

    Webfield.ui.activityList(activityNotes, displayOptions);

    $('.tabs-container a[href="#recent-activity"]').parent().show();
  } else {
    $('.tabs-container a[href="#recent-activity"]').parent().hide();
  }

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
