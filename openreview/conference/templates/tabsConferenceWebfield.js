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
var AUTHOR_SUBMISSION_FIELD = '';

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

// Load makes all the API calls needed to get the data to render the page
// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/
function load() {

  var notesP = $.Deferred().resolve([]);
  var activityNotesP = $.Deferred().resolve([]);
  var authorNotesP = $.Deferred().resolve([]);
  var userGroupsP = $.Deferred().resolve([]);
  var withdrawnNotesP = $.Deferred().resolve([]);
  var deskRejectedNotesP = $.Deferred().resolve([]);

  if (PUBLIC) {
    notesP = Webfield.api.getSubmissions(BLIND_SUBMISSION_ID, {
      pageSize: PAGE_SIZE,
      details: 'replyCount,invitation,original',
      includeCount: true
    });

    if (WITHDRAWN_SUBMISSION_ID) {
      withdrawnNotesP = Webfield.api.getSubmissions(WITHDRAWN_SUBMISSION_ID, {
        pageSize: PAGE_SIZE,
        details: 'replyCount,invitation,original',
        includeCount: true
      });
    }

    if (DESK_REJECTED_SUBMISSION_ID) {
      deskRejectedNotesP = Webfield.api.getSubmissions(DESK_REJECTED_SUBMISSION_ID, {
        pageSize: PAGE_SIZE,
        details: 'replyCount,invitation,original',
        includeCount: true
      });
    }
  }

  if (user && !_.startsWith(user.id, 'guest_')) {
    activityNotesP = Webfield.api.getSubmissions(WILDCARD_INVITATION, {
      pageSize: PAGE_SIZE,
      details: 'forumContent,invitation,writable',
      sort: 'tmdate:desc'
    });

    userGroupsP = Webfield.getAll('/groups', { regex: CONFERENCE_ID + '/.*', member: user.id, web: true });

    var query = {
      pageSize: PAGE_SIZE
    };
    query[AUTHOR_SUBMISSION_FIELD] = user.profile.id;
    authorNotesP = Webfield.api.getSubmissions(SUBMISSION_ID, query);
  }

  return $.when(notesP, userGroupsP, activityNotesP, authorNotesP, withdrawnNotesP, deskRejectedNotesP);
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
  var sections = [
    {
      heading: 'Your Consoles',
      id: 'your-consoles',
    }
  ];

  if (PUBLIC) {
    sections.push({
      heading: 'All Submissions',
      id: 'all-submissions',
    });
    if (WITHDRAWN_SUBMISSION_ID) {
      sections.push({
        heading: 'Withdrawn Submissions',
        id: 'withdrawn-submissions',
      })
    }
    if (DESK_REJECTED_SUBMISSION_ID) {
      sections.push({
        heading: 'Desk Rejected Submissions',
        id: 'desk-rejected-submissions',
      })
    }
  }

  sections.push({
    heading: 'Recent Activity',
    id: 'recent-activity',
  }
)

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
    links.push(
      [
        '<li class="note invitation-link">',
        '<a href="/group?id=' + group + '">' + groupName.replace(/_/g, ' ') + ' Console</a>',
        '</li>'
      ].join('')
    );
  });

  $('#your-consoles .submissions-list').append(links);
}

function renderContent(notesResponse, userGroups, activityNotes, authorNotes, withdrawnNotes, deskRejectedNotes) {

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

  $('#all-submissions').empty();

  if (noteCount) {
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

  var withdrawnNotesCount = withdrawnNotes.count || 0;
  if (withdrawnNotesCount) {
    $('#withdrawn-submissions').empty();

    var withdrawnNotesArray = withdrawnNotes.notes || [];
    Webfield.ui.submissionList(withdrawnNotesArray, {
      heading: null,
      container: '#withdrawn-submissions',
      search: {
        enabled: false
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: withdrawnNotesCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(WITHDRAWN_SUBMISSION_ID, {
          details: 'replyCount,invitation,original',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#withdrawn-submissions"]').parent().hide();
  }

  var deskRejectedNotesCount = deskRejectedNotes.count || 0;
  if (deskRejectedNotesCount) {
    $('#desk-rejected-submissions').empty();

    var deskRejectedNotesArray = deskRejectedNotes.notes || [];
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
          details: 'replyCount,invitation,original',
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
