// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Advanced venue homepage template
//
// This webfield displays the conference header (#header), the submit button (#invitation),
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var PARENT_GROUP_ID = '';
var BLIND_SUBMISSION_ID = '';
var WITHDRAWN_SUBMISSION_ID = '';
var DESK_REJECTED_SUBMISSION_ID = '';
var DECISION_HEADING_MAP = {};
var PAGE_SIZE = 25;

var HEADER = {};

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true
};

var sections = [];
var venueIds = [];

// Main is the entry point to the webfield code and runs everything
function main() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else if (PARENT_GROUP_ID.length){
    OpenBanner.venueHomepageLink(PARENT_GROUP_ID);
  }
  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  renderConferenceHeader();

  renderConferenceTabs();

  load().then(renderContent).then(Webfield.ui.done);
}

// Load makes all the API calls needed to get the data to render the page
function load() {

  var getNotesByVenueId = function() {
    var promises = venueIds.map(function(venueId) {
      return Webfield.api.getSubmissions(BLIND_SUBMISSION_ID, {
        pageSize: PAGE_SIZE,
        'content.venue': venueId,
        details: 'replyCount',
        includeCount: true
      });
    });

    return $.when.apply($, promises).then(function() {
      return _.toArray(arguments);
    });
  };


  var withdrawnNotesP = WITHDRAWN_SUBMISSION_ID ? Webfield.getAll('/notes', {
    invitation: WITHDRAWN_SUBMISSION_ID,
    details: 'replyCount,invitation,original'
  }) : $.Deferred().resolve([]);

  var deskRejectedNotesP = DESK_REJECTED_SUBMISSION_ID ? Webfield.getAll('/notes', {
    invitation: DESK_REJECTED_SUBMISSION_ID,
    details: 'replyCount,invitation,original'
  }) : $.Deferred().resolve([]);

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

  return $.when(getNotesByVenueId(), withdrawnNotesP, deskRejectedNotesP, userGroupsP);
}

function renderConferenceHeader() {
  Webfield.ui.venueHeader(HEADER);
  Webfield.ui.spinner('#notes', { inline: true });
}

function getElementId(decision) {
  if (!decision) return decision;
  return decision.replace(/\W/g, '-')
    .replace('(', '')
    .replace(')', '')
    .toLowerCase();
}

function renderConferenceTabs() {
  sections.push({
    heading: 'Your Consoles',
    id: 'your-consoles',
  });

  var tabNames = []

  Object.keys(DECISION_HEADING_MAP).forEach(function(key) {
    venueIds.push(key);
    sections.push({
      heading: DECISION_HEADING_MAP[key],
      id: getElementId(DECISION_HEADING_MAP[key])
    });
  });

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

function renderNotesbyDecision(submissionCount, submissions, venueId) {
    
  var container = '#' + getElementId(DECISION_HEADING_MAP[venueId])

  $(container).empty();
  if (!submissionCount) return;

  var searchResultsListOptions = Object.assign({}, paperDisplayOptions, {
    container: container,
    autoLoad: false
  });

  Webfield.ui.submissionList(submissions, {
    heading: null,
    container: container,
    search: {
      enabled: true,
      localSearch: false,
      venue: venueId,
      onResults: function(searchResults) {
        Webfield.ui.searchResults(searchResults, searchResultsListOptions);
      },
      onReset: function() {
        Webfield.ui.searchResults(submissions, searchResultsListOptions);
        $(container).append(view.paginationLinks(submissionCount, PAGE_SIZE, 1));
      }
    },
    displayOptions: paperDisplayOptions,
    autoLoad: false,
    noteCount: submissionCount,
    pageSize: PAGE_SIZE,
    onPageClick: function(offset) {
      return Webfield.api.getSubmissions(BLIND_SUBMISSION_ID, {
        'content.venue': venueId,
        details: 'replyCount',
        pageSize: PAGE_SIZE,
        offset: offset
      });
    },
    fadeIn: false
  });
}

function renderContent(notesArray, withdrawnNotes, deskRejectedNotes, userGroups) {

  // Your Consoles Tab
  if (userGroups && userGroups.length) {
    var consoleLinks = createConsoleLinks(userGroups);
    $('#your-consoles').html('<ul class="list-unstyled submissions-list">' +
      consoleLinks.join('\n') + '</ul>');

    $('.tabs-container a[href="#your-consoles"]').parent().show();
  } else {
    $('.tabs-container a[href="#your-consoles"]').parent().hide();
  }

  notesArray.forEach(function(notes, index) {
    renderNotesbyDecision(notes.count, notes.notes, venueIds[index])
  });

  $('#notes > .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
