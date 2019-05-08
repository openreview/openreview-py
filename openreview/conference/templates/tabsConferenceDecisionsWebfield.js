// ------------------------------------
// Advanced venue homepage template
//
// This webfield displays the conference header (#header), the submit button (#invitation),
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var BLIND_SUBMISSION_ID = '';
var WITHDRAWN_INVITATION = '';
var DECISION_INVITATION_REGEX = '';
var DECISION_HEADING_MAP = {};


var HEADER = {};

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  renderConferenceHeader();

  load().then(renderContent).then(Webfield.ui.done);
}

// Load makes all the API calls needed to get the data to render the page
// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/
function load() {
  var notesP = Webfield.getAll('/notes', { invitation: BLIND_SUBMISSION_ID, details: 'replyCount,original' });

  var withdrawnNotesP = WITHDRAWN_INVITATION ? Webfield.getAll('/notes', { invitation: WITHDRAWN_INVITATION, noDetails: true }) : Promise.resolve({ notes: []});

  var decisionNotesP = Webfield.getAll('/notes', { invitation: DECISION_INVITATION_REGEX, noDetails: true });

  return $.when(notesP, withdrawnNotesP, decisionNotesP);
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


function renderContent(notes, withdrawnNotes, decisionsNotes) {

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

  var paperDisplayOptions = {
    pdfLink: true,
    replyCount: true,
    showContents: true
  };

  var activeTab = 0;
  var loadingContent = Handlebars.templates.spinner({ extraClasses: 'spinner-inline' });
  var sections = [];

  for (var decision in DECISION_HEADING_MAP) {
    sections.push({
      heading: DECISION_HEADING_MAP[decision],
      id: getElementId(decision),
      content: loadingContent
    });
  }

  sections[activeTab].active = true;
  sections[activeTab].content = null;

  $('#notes .tabs-container').remove();

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });

  $('#group-container').on('shown.bs.tab', 'ul.nav-tabs li a', function(e) {
    activeTab = $(e.target).data('tabIndex');
    var containerId = sections[activeTab].id;

    setTimeout(function() {
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

  $('#notes > .spinner-container').remove();
  $('.tabs-container').show();

}

// Go!
main();
