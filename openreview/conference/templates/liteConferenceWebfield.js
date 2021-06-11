// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Lite venue homepage template
//
// This webfield is similar to the standard tabbed conference homepage,
// but doesn't include the Activity, Withdrawn Notes, and Desk Rejected
// Notes tabs
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var PARENT_GROUP_ID = '';
var SUBMISSION_ID = '';
var BLIND_SUBMISSION_ID = '';
var WITHDRAWN_SUBMISSION_ID = '';
var DESK_REJECTED_SUBMISSION_ID = '';
var REVIEWERS_NAME = '';
var AREA_CHAIRS_NAME = '';
var AREA_CHAIRS_ID = '';
var REVIEWERS_ID = '';
var PROGRAM_CHAIRS_ID = '';
var AUTHORS_ID = '';
var HEADER = {};
var PUBLIC = false;

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

function load() {
  var notesP = $.Deferred().resolve([]);
  var authorNotesP = $.Deferred().resolve([]);
  var userGroupsP = $.Deferred().resolve([]);

  if (PUBLIC) {
    notesP = Webfield.api.getSubmissions(BLIND_SUBMISSION_ID, {
      pageSize: PAGE_SIZE,
      details: 'replyCount,invitation,original',
      includeCount: true
    });
  }

  if (user && !_.startsWith(user.id, 'guest_')) {
    userGroupsP = Webfield.getAll('/groups', {
      regex: CONFERENCE_ID + '/.*',
      member: user.id,
      web: true
    });

    authorNotesP = Webfield.api.getSubmissions(SUBMISSION_ID, {
      pageSize: PAGE_SIZE,
      'content.authorids': user.profile.id
    });
  }

  return $.when(notesP, userGroupsP, authorNotesP);
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
          if (PUBLIC) {
            promptMessage('Your submission is complete. Check your inbox for a confirmation email. ' +
              'A list of all submissions will be available after the deadline.');
          } else {
            promptMessage('Your submission is complete. Check your inbox for a confirmation email. ' +
              'The author console page for managing your submissions will be available soon.');
          }

          load().then(renderContent).then(function() {
            $('.tabs-container a[href="#your-consoles"]').click();
          });
        }
      });
    });
}

function renderConferenceTabs() {
  var sections = [{
    heading: 'Your Consoles',
    id: 'your-consoles',
  }];

  if (PUBLIC) {
    sections.push({
      heading: 'All Submissions',
      id: 'all-submissions',
    });
  }

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });
}

function createConsoleLinks(allGroups) {
  var uniqueGroups = _.sortBy(_.uniq(allGroups));
  var links = [];
  uniqueGroups.forEach(function(group) {
    var groupName = group.split('/').pop();
    if (groupName.slice(-1) === 's') {
      groupName = groupName.slice(0, -1);
    }
    links.push([
      '<li class="note invitation-link">',
        '<a href="/group?id=' + group + '">' + groupName.replace(/_/g, ' ') + ' Console</a>',
      '</li>'
    ].join(''));
  });

  $('#your-consoles .submissions-list').append(links);
}

function renderContent(notesResponse, userGroups, authorNotes) {

  // Your Consoles tab
  if (userGroups.length || authorNotes.length) {
    var $container = $('#your-consoles').empty();
    $container.append('<ul class="list-unstyled submissions-list">');

    var allConsoles = [];
    if (authorNotes.length) {
      allConsoles.push(AUTHORS_ID);
    }
    userGroups.forEach(function(group) {
      allConsoles.push(group.id);
    });

    // Render all console links for the user
    createConsoleLinks(allConsoles);

    $('.tabs-container a[href="#your-consoles"]').parent().show();
  } else {
    $('.tabs-container a[href="#your-consoles"]').parent().hide();
  }

  // All Submitted Papers tab
  var notes = notesResponse.notes || [];
  var noteCount = notesResponse.count || 0;

  if (noteCount) {
    $('#all-submissions').empty();

    var searchResultsListOptions = _.assign({}, paperDisplayOptions, {
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
        }
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: noteCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(BLIND_SUBMISSION_ID, {
          details: 'replyCount,invitation,original',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#all-submissions"]').parent().hide();
  }

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
