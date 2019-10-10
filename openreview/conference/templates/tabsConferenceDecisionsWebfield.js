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
// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/
function load() {

  var notesP = Webfield.getAll(
    '/notes',
    {
      invitation: BLIND_SUBMISSION_ID,
      details: 'replyCount,original'
    }
  )

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

  var decisionNotesP = Webfield.getAll('/notes', { invitation: DECISION_INVITATION_REGEX, noDetails: true });

  return $.when(notesP, decisionNotesP, withdrawnNotesP, deskRejectedNotesP);
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

function renderContent(notes, decisionsNotes, withdrawnNotes, deskRejectedNotes) {

  var notesDict = {};
  _.forEach(notes, function(n) {
    notesDict[n.id] = n;
  });
  var papersByDecision = {};

  for (var decision in DECISION_HEADING_MAP) {
    papersByDecision[decision] = [];
  }

  _.forEach(decisionsNotes, function(d) {
    if (_.has(notesDict, d.forum)) {
      papersByDecision[d.content.decision].push(notesDict[d.forum]);
    }
  });
  for (var decision in DECISION_HEADING_MAP) {
    papersByDecision[getElementId(decision)] = _.sortBy(papersByDecision[decision], function(o) { return o.id; });
  }

  $('#group-container').on('shown.bs.tab', 'ul.nav-tabs li a', function(e) {
    var activeTab = 0;
    activeTab = $(e.target).data('tabIndex');
    var containerId = sections[activeTab].id;
    setTimeout(function() {
      if (activeTab < Object.keys(DECISION_HEADING_MAP).length) {
        Webfield.ui.searchResults(
          papersByDecision[containerId],
          _.assign({}, paperDisplayOptions, {showTags: false, container: '#' + containerId})
        );
      }
    }, 100);
  });

  var withdrawnNotesCount = withdrawnNotes.count || 0;
  if (WITHDRAWN_SUBMISSION_ID && withdrawnNotesCount) {

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

  var deskRejectedNotesCount = deskRejectedNotes.count || 0;
  if (DESK_REJECTED_SUBMISSION_ID && deskRejectedNotesCount) {

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

  $('#group-container').on('hidden.bs.tab', 'ul.nav-tabs li a', function(e) {
    var containerId = $(e.target).attr('href');
    Webfield.ui.spinner(containerId, {inline: true});
  });

  $('#notes > .spinner-container').remove();
  $('.tabs-container').show();

}

// Go!
main();
