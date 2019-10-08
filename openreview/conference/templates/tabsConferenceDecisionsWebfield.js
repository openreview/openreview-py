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

  var notesP = Webfield.api.getSubmissions(BLIND_SUBMISSION_ID, {
    pageSize: PAGE_SIZE,
    details: 'replyCount,original',
    includeCount: true
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
    })
  }
  if (DESK_REJECTED_SUBMISSION_ID) {
    sections.push({
      heading: 'Desk Rejected Submissions',
      id: 'desk-rejected-submissions',
    })
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

  var activeTab = 0;
  // var loadingContent = Handlebars.templates.spinner({ extraClasses: 'spinner-inline' });
  // var sections = [];

  // for (var decision in DECISION_HEADING_MAP) {
  //   sections.push({
  //     heading: DECISION_HEADING_MAP[decision],
  //     id: getElementId(decision),
  //     content: loadingContent
  //   });
  // }


  // sections[activeTab].active = true;
  // sections[activeTab].content = null;

  // $('#notes .tabs-container').remove();

  // Webfield.ui.tabPanel(sections, {
  //   container: '#notes',
  //   hidden: true
  // });

  $('#group-container').on('shown.bs.tab', 'ul.nav-tabs li a', function(e) {
    activeTab = $(e.target).data('tabIndex');
    var containerId = sections[activeTab].id;

    setTimeout(function() {
      console.log('timing out!!');
      Webfield.ui.searchResults(
        papersByDecision[containerId],
        _.assign({}, paperDisplayOptions, {showTags: false, container: '#' + containerId})
      );
    }, 100);
  });

  $('#group-container').on('hidden.bs.tab', 'ul.nav-tabs li a', function(e) {
    var containerId = $(e.target).attr('href');
    Webfield.ui.spinner(containerId, {inline: true});
  });

  Webfield.ui.searchResults(
    papersByDecision[sections[activeTab].id],
    _.assign({}, paperDisplayOptions, {showTags: false, container: '#' + sections[activeTab].id})
  );

  var withdrawnNotesCount = withdrawnNotes.count || 0;
  if (withdrawnNotesCount) {
    $('#withdrawn-submissions').empty();

    var withdrawnNotesArray = withdrawnNotes.notes || [];
    console.log('withdrawn notes:');
    console.log(withdrawnNotesArray);
    Webfield.ui.submissionList(withdrawnNotesArray, {
      heading: null,
      container: '#withdrawn-submissions',
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: withdrawnNotesCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(WITHDRAWN_SUBMISSION_ID, {
          details: 'replyCount,original',
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
    console.log('desk rej notes:');
    console.log(deskRejectedNotesArray);
    Webfield.ui.submissionList(deskRejectedNotesArray, {
      heading: null,
      container: '#desk-rejected-submissions',
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: deskRejectedNotesCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(DESK_REJECTED_SUBMISSION_ID, {
          details: 'replyCount,original',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#desk-rejected-submissions"]').parent().hide();
  }

  $('#notes > .spinner-container').remove();
  $('.tabs-container').show();

}

// Go!
main();
