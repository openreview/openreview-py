// ------------------------------------
// Venue homepage template
//
// This webfield displays the conference header (#header), the submit button (#invitation),
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var ARTICLE_ID = '';
var DESK_REJECTED_SUBMISSION_ID = '';
var HEADER = {};

var WILDCARD_INVITATION = CONFERENCE_ID + '/.*';
var BUFFER = 0;  // deprecated
var PAGE_SIZE = 50;

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true,
  showTags: false
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

  var articleNotesP = Webfield.api.getSubmissions(ARTICLE_ID, {
    pageSize: PAGE_SIZE,
    details: 'replyCount,invitation',
    includeCount: true
  });

  var submissionNotesP = Webfield.api.getSubmissions(SUBMISSION_ID, {
    pageSize: PAGE_SIZE,
    details: 'replyCount,invitation',
    includeCount: true
  });

  var deskRejectedNotesP = Webfield.api.getSubmissions(DESK_REJECTED_SUBMISSION_ID, {
    pageSize: PAGE_SIZE,
    details: 'replyCount,invitation',
    includeCount: true
  });

  var activityNotesP = $.Deferred().resolve([]);
  if (user && !_.startsWith(user.id, 'guest_')) {
    activityNotesP = Webfield.api.getSubmissions(WILDCARD_INVITATION, {
      pageSize: PAGE_SIZE,
      details: 'forumContent,invitation,writable',
      sort: 'tmdate:desc'
    });
  }

  return $.when(articleNotesP, submissionNotesP, deskRejectedNotesP, activityNotesP);
}

// Render functions
function renderConferenceHeader() {
  Webfield.ui.venueHeader(HEADER);

  Webfield.ui.spinner('#notes', { inline: true });
}

function renderSubmissionButton() {
  Webfield.api.getSubmissionInvitation(SUBMISSION_ID, {deadlineBuffer: BUFFER})
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

  var sections = [{
    heading: 'Articles',
    id: 'articles',
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

function renderContent(articlesResponse, submissionsResponse, deskRejectedResponse, activityNotes) {

  var notes = articlesResponse.notes || [];
  var noteCount = articlesResponse.count || 0;

  $('#articles').empty();

  if (noteCount) {
    var searchResultsListOptions = _.assign({}, paperDisplayOptions, {
      container: '#articles',
      autoLoad: false
    });

    Webfield.ui.submissionList(notes, {
      heading: null,
      container: '#articles',
      search: {
        enabled: true,
        localSearch: false,
        invitation: ARTICLE_ID,
        onResults: function(searchResults) {
          Webfield.ui.searchResults(searchResults, searchResultsListOptions);
        },
        onReset: function() {
          Webfield.ui.searchResults(notes, searchResultsListOptions);
          $('#articles').append(view.paginationLinks(noteCount, PAGE_SIZE, 1));
        }
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: noteCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(ARTICLE_ID, {
          details: 'replyCount,invitation',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#articles"]').parent().hide();
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

  var submissionNotesCount = submissionsResponse.count || 0;
  if (submissionNotesCount) {
    $('#submissions').empty();

    var notes = submissionsResponse.notes || [];
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
          details: 'replyCount,invitation',
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
        return Webfield.api.getSubmissions(DESK_REJECTED_SUBMISSION_ID, {
          details: 'replyCount,invitation',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#desk-rejected-submissions"]').parent().hide();
  }

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
