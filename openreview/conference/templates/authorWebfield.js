// ------------------------------------
// Author Console Webfield
//
// This webfield displays the conference header (#header), the submit button (#invitation),
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var SUBMISSION_ID = '';
var HEADER_TEXT = '';
var INSTRUCTIONS = '';
var SCHEDULE_HTML = '';

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showActionButtons: true,
  showContents: true
};


// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  Webfield.ui.header(HEADER_TEXT, INSTRUCTIONS);

  renderConferenceTabs();

  load().then(renderContent).then(Webfield.ui.done);

  OpenBanner.venueHomepageLink(CONFERENCE_ID);
}


// Load makes all the API calls needed to get the data to render the page
// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/
function load() {

  var authorNotesP;
  var invitationsP;
  var tagInvitationsP;

  if (!user) {
    authorNotesP = $.Deferred().resolve([]);
    invitationsP = $.Deferred().resolve([]);
    tagInvitationsP = $.Deferred().resolve([]);

  } else {
    authorNotesP = Webfield.get('/notes', {
      'content.authorids': user.profile.id,
      invitation: SUBMISSION_ID,
      details: 'replyCount,writable'
    }).then(function(result) {
      return result.notes;
    });

    invitationsP = Webfield.get('/invitations', {
      invitation: CONFERENCE_ID + '/-/.*',
      invitee: true,
      duedate: true,
      replyto: true,
      details:'replytoNote,repliedNotes'
    }).then(function(result) {
      return _.filter(result.invitations, function(i) {
        return i.id.startsWith(CONFERENCE_ID);
      });
    });

    tagInvitationsP = Webfield.get('/invitations', {
      invitation: CONFERENCE_ID + '/-/.*',
      invitee: true,
      duedate: true,
      tags: true,
      details:'repliedTags'
    }).then(function(result) {
      return result.invitations;
    });
  }

  return $.when(authorNotesP, invitationsP, tagInvitationsP);
}


// Render functions
function renderConferenceTabs() {
  var sections = [
    {
      heading: 'Author Schedule',
      id: 'author-schedule',
      content: SCHEDULE_HTML
    },
    {
      heading: 'Author Tasks',
      id: 'author-tasks'
    },
    {
      heading: 'Your Submissions',
      id: 'your-submissions',
    }
  ];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });
}


function renderContent(authorNotes, invitations, tagInvitations) {
  // Author Tasks tab
  var tasksOptions = {
    container: '#author-tasks',
    emptyMessage: 'No outstanding tasks for this conference'
  }
  $(tasksOptions.container).empty();

  // Filter out non-author tasks
  var filterFunc = function(inv) {
    return _.some(inv.invitees, function(invitee) {
      return invitee.indexOf('Authors') !== -1;
    });
  };
  var authorInvitations = _.filter(invitations, filterFunc);
  var authorTagInvitations = _.filter(tagInvitations, filterFunc);

  Webfield.ui.newTaskList(authorInvitations, authorTagInvitations, tasksOptions)
  $('.tabs-container a[href="#author-tasks"]').parent().show();

  // Your Private Versions and Your Anonymous Versions tabs
  if (authorNotes.length) {
    Webfield.ui.submissionList(authorNotes, {
      heading: null,
      container: '#your-submissions',
      search: { enabled: false },
      displayOptions: paperDisplayOptions
    });

    $('.tabs-container a[href="#your-submissions"]').parent().show();
  } else {
    $('.tabs-container a[href="#your-submissions"]').parent().hide();
  }

  // Remove spinner and show content
  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
