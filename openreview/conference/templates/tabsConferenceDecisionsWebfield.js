// ------------------------------------
// Advanced venue homepage template
//
// This webfield displays the conference header (#header), the submit button (#invitation),
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var BLIND_SUBMISSION_ID = '';
var WITHDRAWN_SUBMISSION_ID = '';
var DESK_REJECTED_SUBMISSION_ID = '';
var DECISION_INVITATION_REGEX = '';
var DECISION_HEADING_MAP = {};
var PAGE_SIZE = 25;

var HEADER = {};

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true
};

var sections = [];

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  renderConferenceHeader();

  renderConferenceTabs();

  load().then(renderContent).then(Webfield.ui.done);
}

// Load makes all the API calls needed to get the data to render the page
function load() {
  var notesP = Webfield.getAll('/notes', {
    invitation: BLIND_SUBMISSION_ID,
    details: 'replyCount,original'
  });

  var withdrawnNotesP = WITHDRAWN_SUBMISSION_ID ? Webfield.api.getSubmissions(WITHDRAWN_SUBMISSION_ID, {
    pageSize: PAGE_SIZE,
    noDetails: true,
    includeCount: true
  }) : $.Deferred().resolve([]);

  var deskRejectedNotesP = DESK_REJECTED_SUBMISSION_ID ? Webfield.api.getSubmissions(DESK_REJECTED_SUBMISSION_ID, {
    pageSize: PAGE_SIZE,
    noDetails: true,
    includeCount: true
  }) : $.Deferred().resolve([]);

  var decisionNotesP = Webfield.getAll('/notes', {
    invitation: DECISION_INVITATION_REGEX,
    noDetails: true
  });

  var userGroupsP;
  if (!user || _.startsWith(user.id, 'guest_')) {
    userGroupsP = $.Deferred().resolve([]);
  } else {
    userGroupsP = Webfield.getAll('/groups', {
      regex: CONFERENCE_ID + '/.*',
      member: user.id,
      web: true
    }).then(function(groups) {
      if (!groups || !groups.length) {
        return [];
      }

      return groups.map(function(g) { return g.id; });
    });
  }

  return $.when(notesP, decisionNotesP, withdrawnNotesP, deskRejectedNotesP, userGroupsP);
}

function renderConferenceHeader() {
  Webfield.ui.venueHeader(HEADER);
  Webfield.ui.spinner('#notes', { inline: true });
}

function getElementId(decision) {
  return decision.replace(' ', '-')
    .replace('(', '')
    .replace(')', '')
    .toLowerCase();
}

function renderConferenceTabs() {
  sections.push({
    heading: 'Your Consoles',
    id: 'your-consoles',
  });
  for (var decision in DECISION_HEADING_MAP) {
    sections.push({
      heading: DECISION_HEADING_MAP[decision],
      id: getElementId(decision)
    });
  }
  if (WITHDRAWN_SUBMISSION_ID) {
    sections.push({
      heading: 'Withdrawn Submissions',
      id: 'withdrawn-submissions',
    });
  }
  if (DESK_REJECTED_SUBMISSION_ID) {
    sections.push({
      heading: 'Desk Rejected Submissions',
      id: 'desk-rejected-submissions',
    });
  }

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });
}

function createConsoleLinks(allGroups) {
  var uniqueGroups = _.sortedUniq(allGroups.sort());

  return uniqueGroups.map(function(group) {
    var groupName = group.split('/').pop();
    if (groupName.slice(-1) === 's') {
      groupName = groupName.slice(0, -1);
    }

    return [
      '<li class="note invitation-link">',
        '<a href="/group?id=' + group + '">' + groupName.replace(/_/g, ' ') + ' Console</a>',
      '</li>'
    ].join('');
  });
}

function groupNotesByDecision(notes, decisionNotes) {
  // Categorize notes into buckets defined by DECISION_HEADING_MAP
  var notesDict = _.keyBy(notes, 'id');

  var papersByDecision = {};
  for (var decision in DECISION_HEADING_MAP) {
    papersByDecision[getElementId(decision)] = [];
  }

  decisionNotes.forEach(function(d) {
    var decisionKey = getElementId(d.content.decision);
    if (notesDict[d.forum] && papersByDecision[decisionKey]) {
      papersByDecision[decisionKey].push(notesDict[d.forum]);
    }
  });

  return papersByDecision;
}

function renderContent(notes, decisionNotes, withdrawnNotes, deskRejectedNotes, userGroups) {
  var papersByDecision = groupNotesByDecision(notes, decisionNotes);

  // Your Consoles Tab
  if (userGroups && userGroups.length) {
    var consoleLinks = createConsoleLinks(userGroups);
    $('#your-consoles').html('<ul class="list-unstyled submissions-list">' +
      consoleLinks.join('\n') + '</ul>');

    $('.tabs-container a[href="#your-consoles"]').parent().show();
  } else {
    $('.tabs-container a[href="#your-consoles"]').parent().hide();
  }

  // Withdrawn Submissions Tab
  if (WITHDRAWN_SUBMISSION_ID && withdrawnNotes.count) {
    $('#withdrawn-submissions').empty();

    Webfield.ui.submissionList(withdrawnNotes.notes, {
      heading: null,
      container: '#withdrawn-submissions',
      search: {
        enabled: false
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: withdrawnNotes.count,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(WITHDRAWN_SUBMISSION_ID, {
          noDetails: true,
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#withdrawn-submissions"]').parent().hide();
  }

  // Desk Rejected Submissions Tab
  if (DESK_REJECTED_SUBMISSION_ID && deskRejectedNotes.count) {
    $('#desk-rejected-submissions').empty();

    Webfield.ui.submissionList(deskRejectedNotes.notes, {
      heading: null,
      container: '#desk-rejected-submissions',
      search: {
        enabled: false
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: deskRejectedNotes.count,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(DESK_REJECTED_SUBMISSION_ID, {
          noDetails: true,
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#desk-rejected-submissions"]').parent().hide();
  }

  // Register event handlers
  $('#group-container').on('shown.bs.tab', 'ul.nav-tabs li a', function(e) {
    var containerSelector = $(e.target).attr('href');
    var containerId = containerSelector.substring(1);
    if (!papersByDecision.hasOwnProperty(containerId) || !$(containerSelector).length) {
      return;
    }

    setTimeout(function() {
      Webfield.ui.searchResults(
        papersByDecision[containerId],
        Object.assign({}, paperDisplayOptions, { showTags: false, container: containerSelector })
      );
    }, 150);
  });

  $('#group-container').on('hidden.bs.tab', 'ul.nav-tabs li a', function(e) {
    var containerSelector = $(e.target).attr('href');
    var containerId = containerSelector.substring(1);
    if (!papersByDecision.hasOwnProperty(containerId) || !$(containerSelector).length) {
      return;
    }

    Webfield.ui.spinner(containerSelector, { inline: true });
  });

  $('#notes > .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
