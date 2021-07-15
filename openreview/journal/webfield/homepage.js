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

  var submittedNotesP = Webfield.api.getSubmissionsV2(SUBMISSION_ID, {
    'content.venueid': SUBMITTED_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var underReviewNotesP = Webfield.api.getSubmissionsV2(SUBMISSION_ID, {
    'content.venueid': UNDER_REVIEW_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var rejectedNotesP = Webfield.api.getSubmissionsV2(SUBMISSION_ID, {
    'content.venueid': DESK_REJECTED_ID + ',' + REJECTED_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var acceptedNotesP = Webfield.api.getSubmissionsV2(SUBMISSION_ID, {
    'content.venueid': CONFERENCE_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var activityNotesP = $.Deferred().resolve([]);
  if (user && !_.startsWith(user.id, 'guest_')) {
    activityNotesP = Webfield.api.getSubmissionsV2(WILDCARD_INVITATION, {
      pageSize: PAGE_SIZE,
      details: 'forumContent,writable'
    });
  }

  return $.when(acceptedNotesP, submittedNotesP, underReviewNotesP, rejectedNotesP, activityNotesP);
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

function renderContent(acceptedResponse, submittedResponse, underReviewResponse, rejectedResponse, activityNotes) {

  var acceptedPapers = acceptedResponse.notes || [];
  var acceptedPapersCount = acceptedResponse.count || 0;

  $('#accepted-papers').empty();

  if (acceptedPapersCount) {
    var searchResultsListOptions = _.assign({}, paperDisplayOptions, {
      container: '#accepted-papers',
      autoLoad: false
    });

    Webfield.ui.submissionListV2(acceptedPapers, {
      heading: null,
      container: '#accepted-papers',
      search: {
        enabled: true,
        localSearch: false,
        invitation: SUBMISSION_ID,
        onResults: function(searchResults) {
          Webfield.ui.searchResults(searchResults, searchResultsListOptions);
        },
        onReset: function() {
          Webfield.ui.searchResults(notes, searchResultsListOptions);
          $('#accepted-papers').append(view.paginationLinks(acceptedPapersCount, PAGE_SIZE, 1));
        }
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: acceptedPapersCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissionsV2(SUBMISSION_ID, {
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

    Webfield.ui.submissionListV2(underReviewSubmissions, {
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
        return Webfield.api.getSubmissionsV2(SUBMISSION_ID, {
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
    Webfield.ui.submissionListV2(notes, {
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
        return Webfield.api.getSubmissionsV2(SUBMISSION_ID, {
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
    Webfield.ui.submissionListV2(rejectedNotesArray, {
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
        return Webfield.api.getSubmissionsV2(SUBMISSION_ID, {
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

  // Activity Tab
  if (activityNotes.length) {
    var displayOptions = {
      container: '#recent-activity',
      user: user && user.profile,
      showActionButtons: true
    };

    $(displayOptions.container).empty();

    Webfield.ui.activityListV2(activityNotes, displayOptions);

    $('.tabs-container a[href="#recent-activity"]').parent().show();
  } else {
    $('.tabs-container a[href="#recent-activity"]').parent().hide();
  }

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
