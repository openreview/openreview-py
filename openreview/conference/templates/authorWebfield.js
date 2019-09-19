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
      details: 'replyCount,writable'
    }).then(function(result) {
      return result.notes;
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
    emptyMessage: 'No outstanding tasks for this conference'
  }
  $(tasksOptions.container).empty();

  Webfield.ui.newTaskList(invitations, edgeInvitations, tasksOptions);

  // Your Private Versions and Your Anonymous Versions tabs
  Webfield.ui.submissionList(authorNotes, {
    heading: null,
    container: '#your-submissions',
    search: { enabled: false },
    fadeIn: false,
    displayOptions: paperDisplayOptions
  });

  // Remove spinner and show content
  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
