// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Basic venue homepage template
//
// This webfield displays the conference header (#header), the submit button
// (#invitation), and a list of all submitted papers (#notes).
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var PARENT_GROUP_ID = '';
var BLIND_SUBMISSION_ID = '';
var HEADER = {};

var BUFFER = 1000 * 60 * 30;  // deprecated
var PAGE_SIZE = 50;

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true,
  showTags: true
};


// Main is the entry point to the webfield code and runs everything
function main() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else if (PARENT_GROUP_ID.length){
    OpenBanner.venueHomepageLink(PARENT_GROUP_ID);
  }
  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  renderConferenceHeader();

  renderSubmissionButton();

  renderConferenceTabs();

  load().then(renderContent).then(Webfield.ui.done);
}

// Load makes all the API calls needed to get the data to render the page
// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/
function load() {
  var notesP = Webfield.api.getSubmissions(BLIND_SUBMISSION_ID, {
    pageSize: PAGE_SIZE,
    includeCount: true
  });
  var tagInvitationsP;

  if (!user || _.startsWith(user.id, 'guest_')) {
    tagInvitationsP = $.Deferred().resolve([]);
  } else {
    tagInvitationsP = Webfield.get('/invitations', { replyInvitation: BLIND_SUBMISSION_ID, tags: true })
    .then(function(result) {
      return result.invitations;
    });
  }

  return $.when(
    notesP, tagInvitationsP
  );
}

// Render functions
function renderConferenceHeader() {
  Webfield.ui.venueHeader(HEADER);
  Webfield.ui.spinner('#notes', { inline: true });
}

function renderSubmissionButton() {
  Webfield.api.getSubmissionInvitation(BLIND_SUBMISSION_ID, {deadlineBuffer: BUFFER})
    .then(function(invitation) {
      Webfield.ui.submissionButton(invitation, user, {
        onNoteCreated: function() {
          // Callback funtion to be run when a paper has successfully been submitted (required)
          promptMessage('Your artifact submission is complete. Check your inbox for a confirmation email.');
          load().then(renderContent);
        }
      });
    });
}

function renderConferenceTabs() {
  var sections = [
    {
      heading: 'All Submissions',
      id: 'all-submissions',
    }
  ];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });
}

function renderContent(notesResponse, tagInvitations) {
  var notes = notesResponse.notes || [];
  var noteCount = notesResponse.count || 0;

  // All Submitted Papers tab
  $('#all-submissions').empty();

  if (noteCount) {
    var searchResultsListOptions = _.assign({}, paperDisplayOptions, {
      tagInvitations: tagInvitations,
      container: '#all-submissions',
      autoLoad: false
    });

    Webfield.ui.submissionList(notes, {
      heading: null,
      container: '#all-submissions',
      search: {
        enabled: true,
        localSearch: false,
        invitation: BLIND_SUBMISSION_ID,
        onResults: function(searchResults) {
          Webfield.ui.searchResults(searchResults, searchResultsListOptions);
        },
        onReset: function() {
          Webfield.ui.searchResults(notes, searchResultsListOptions);
          $('#all-submissions').append(view.paginationLinks(noteCount, PAGE_SIZE, 1));
        },
      },
      displayOptions: _.assign({}, paperDisplayOptions, { tagInvitations: tagInvitations }),
      autoLoad: false,
      noteCount: noteCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(BLIND_SUBMISSION_ID, {
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });

    $('.tabs-container a[href="#all-submissions"]').parent().show();
  } else {
    $('.tabs-container a[href="#all-submissions"]').parent().hide();
  }

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
