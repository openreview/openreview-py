// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Venue homepage template
//
// This webfield displays the conference header (#header), the submit button (#invitation),
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var SUBMITTED_ID = '';
var UNDER_REVIEW_ID = '';
var DESK_REJECTED_ID = '';
var REJECTED_ID = '';
var HEADER = {};

var WILDCARD_INVITATION = CONFERENCE_ID + '/.*';
var PAGE_SIZE = 50;

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true,
  showTags: false,
  referrer: encodeURIComponent('[' + HEADER.short + '](/group?id=' + CONFERENCE_ID + ')')
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

  var submittedNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': SUBMITTED_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var underReviewNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': UNDER_REVIEW_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var rejectedNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': DESK_REJECTED_ID + ',' + REJECTED_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var acceptedNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': CONFERENCE_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  return $.when(acceptedNotesP, submittedNotesP, underReviewNotesP, rejectedNotesP);
}

// Render functions
function renderConferenceHeader() {
  Webfield.ui.venueHeader(HEADER);

  Webfield.ui.spinner('#notes', { inline: true });
}

function renderSubmissionButton() {
  Webfield2.ui.renderInvitationButton('#invitation', SUBMISSION_ID, {
    onNoteCreated: function() {
      // Callback funtion to be run when a paper has successfully been submitted (required)
      promptMessage('Your submission is complete. Check your inbox for a confirmation email. ');

      load().then(renderContent).then(function() {
        $('.tabs-container a[href="#your-consoles"]').click();
      });
    }
  });
}

function renderConferenceTabs() {

  var sections = [
  {
      heading: 'Accepted Papers',
      id: 'accepted-papers',
  },
  {
    heading: 'Under Review',
    id: 'under-review-submissions',
  },
  {
    heading: 'Submissions',
    id: 'submissions',
  },
  {
    heading: 'Rejected Submissions',
    id: 'rejected-submissions',
  }];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });
}

function renderContent(acceptedResponse, submittedResponse, underReviewResponse, rejectedResponse) {

  var acceptedPapers = acceptedResponse.notes || [];
  var acceptedPapersCount = acceptedResponse.count || 0;

  $('#accepted-papers').empty();

  if (acceptedPapersCount) {
    var searchResultsListOptions = _.assign({}, paperDisplayOptions, {
      container: '#accepted-papers',
      autoLoad: false
    });

    Webfield2.ui.submissionList(acceptedPapers, {
      heading: null,
      container: '#accepted-papers',
      search: {
        enabled: true,
        localSearch: false,
        invitation: SUBMISSION_ID,
        onResults: function(searchResults) {
          Webfield2.ui.searchResults(searchResults, searchResultsListOptions);
        },
        onReset: function() {
          Webfield2.ui.searchResults(notes, searchResultsListOptions);
          $('#accepted-papers').append(view.paginationLinks(acceptedPapersCount, PAGE_SIZE, 1));
        }
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: acceptedPapersCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield2.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': CONFERENCE_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#accepted-papers"]').parent().hide();
  }

  var underReviewSubmissions = underReviewResponse.notes || [];
  var underReviewCount = underReviewResponse.count || 0;

  $('#under-review-submissions').empty();

  if (underReviewCount) {
    var searchResultsListOptions = _.assign({}, paperDisplayOptions, {
      container: '#under-review-submissions',
      autoLoad: false
    });

    Webfield2.ui.submissionList(underReviewSubmissions, {
      heading: null,
      container: '#under-review-submissions',
      search: {
        enabled: true,
        localSearch: false,
        invitation: SUBMISSION_ID,
        onResults: function(searchResults) {
          Webfield2.ui.searchResults(searchResults, searchResultsListOptions);
        },
        onReset: function() {
          Webfield2.ui.searchResults(notes, searchResultsListOptions);
          $('#under-review-submissions').append(view.paginationLinks(underReviewCount, PAGE_SIZE, 1));
        }
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: underReviewCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield2.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': UNDER_REVIEW_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#under-review-submissions"]').parent().hide();
  }

  var submissionNotesCount = submittedResponse.count || 0;
  if (submissionNotesCount) {
    $('#submissions').empty();

    var notes = submittedResponse.notes || [];
    Webfield2.ui.submissionList(notes, {
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
        return Webfield2.api.getSubmissions(SUBMISSION_ID, {
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

  var rejectedNotesCount = rejectedResponse.count || 0;
  if (rejectedNotesCount) {
    $('#rejected-submissions').empty();

    var rejectedNotesArray = rejectedResponse.notes || [];
    Webfield2.ui.submissionList(rejectedNotesArray, {
      heading: null,
      container: '#rejected-submissions',
      search: {
        enabled: false
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: rejectedNotesCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield2.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': REJECTED_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#rejected-submissions"]').parent().hide();
  }

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
