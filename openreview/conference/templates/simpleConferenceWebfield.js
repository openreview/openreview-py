// ------------------------------------
// Basic venue homepage template
//
// This webfield displays the conference header (#header), the submit button
// (#invitation), and a list of all submitted papers (#notes).
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var HEADER = {};

var BUFFER = 1000 * 60 * 30;  // 30 minutes
var PAGE_SIZE = 50;

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true
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
  var notesP = Webfield.api.getSubmissions(SUBMISSION_ID, {
    pageSize: PAGE_SIZE,
    details: 'replyCount,tags'
  });
  var tagInvitationsP;

  if (!user || _.startsWith(user.id, 'guest_')) {
    tagInvitationsP = $.Deferred().resolve([]);
  } else {
    tagInvitationsP = Webfield.get('/invitations', { replyInvitation: SUBMISSION_ID, tags: true })
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
  Webfield.api.getSubmissionInvitation(SUBMISSION_ID, {deadlineBuffer: BUFFER})
    .then(function(invitation) {
      Webfield.ui.submissionButton(invitation, user, {
        onNoteCreated: function() {
          // Callback funtion to be run when a paper has successfully been submitted (required)
          promptMessage('Your artifact submission is complete. Check your inbox for a confirmation email.');
          load().then(renderContent).then(Webfield.ui.done);
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

function renderContent(notes, tagInvitations) {
  // All Submitted Papers tab
  var submissionListOptions = _.assign({}, paperDisplayOptions, {
    showTags: true,
    tagInvitations: tagInvitations,
    container: '#all-submissions'
  });

  $(submissionListOptions.container).empty();

  if (notes.length){
    Webfield.ui.submissionList(notes, {
      heading: null,
      container: '#all-submissions',
      search: {
        enabled: true,
        localSearch: false,
        onResults: function(searchResults) {
          var originalSearchResults = searchResults.filter(function(note) {
            return note.invitation === SUBMISSION_ID;
          });
          Webfield.ui.searchResults(originalSearchResults, submissionListOptions);
          Webfield.disableAutoLoading();
        },
        onReset: function() {
          Webfield.ui.searchResults(notes, submissionListOptions);
          if (notes.length === PAGE_SIZE) {
            Webfield.setupAutoLoading(SUBMISSION_ID, PAGE_SIZE, submissionListOptions);
          }
        }
      },
      displayOptions: submissionListOptions,
      fadeIn: false
    });

    if (notes.length === PAGE_SIZE) {
      Webfield.setupAutoLoading(SUBMISSION_ID, PAGE_SIZE, submissionListOptions);
    }
    $('.tabs-container a[href="#all-submissions"]').parent().show();
  } else {
    $('.tabs-container a[href="#all-submissions"]').parent().hide();
  }

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
  Webfield.ui.done();
}

// Go!
main();
