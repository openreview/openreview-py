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
  var notesP = Webfield.getAll('/notes', { invitation: BLIND_SUBMISSION_ID, details: 'replyCount' });

  var withdrawnNotesP = WITHDRAWN_INVITATION ? Webfield.getAll('/notes', { invitation: WITHDRAWN_INVITATION, noDetails: true }) : Promise.resolve({ notes: []});

  var decisionNotesP = Webfield.getAll('/notes', { invitation: DECISION_INVITATION_REGEX, noDetails: true });

  return $.when(notesP, withdrawnNotesP, decisionNotesP);
}

function renderConferenceHeader() {
    Webfield.ui.venueHeader(HEADER);

    Webfield.ui.spinner('#notes', { inline: true });
 }


function renderContent(notes, withdrawnNotes, decisionsNotes) {

  var notesDict = {};
  _.forEach(notes, function(n) {
    notesDict[n.id] = n;
  });

  var oralDecisions = [];
  var posterDecisions = [];
  var submittedPapers = withdrawnNotes;

  _.forEach(decisionsNotes, function(d) {

    if (_.has(notesDict, d.forum)) {
      if (d.content.decision === 'Accept (Oral)') {
        oralDecisions.push(notesDict[d.forum]);
      } else if (d.content.decision === 'Accept (Poster)') {
        posterDecisions.push(notesDict[d.forum]);
      } else if (d.content.decision === 'Reject') {
        submittedPapers.push(notesDict[d.forum]);
      }
    }
  });

  oralDecisions = _.sortBy(oralDecisions, function(o) { return o.id; });
  posterDecisions = _.sortBy(posterDecisions, function(o) { return o.id; });
  submittedPapers = _.sortBy(submittedPapers, function(o) { return o.id; });

  var papers = {
    'accepted-oral-papers': oralDecisions,
    'accepted-poster-papers': posterDecisions,
    'rejected-papers': submittedPapers
  }

  var paperDisplayOptions = {
    pdfLink: true,
    replyCount: true,
    showContents: true
  };

  var activeTab = 0;
  var loadingContent = Handlebars.templates.spinner({ extraClasses: 'spinner-inline' });
  var sections = [
    {
      heading: 'Oral Presentations',
      id: 'accepted-oral-papers',
      content: null
    },
    {
      heading: 'Poster Presentations',
      id: 'accepted-poster-papers',
      content: loadingContent
    },
    {
      heading: 'Submitted Papers',
      id: 'rejected-papers',
      content: loadingContent
    }
  ];

  sections[activeTab].active = true;

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
        papers[containerId],
        _.assign({}, paperDisplayOptions, {showTags: false, container: '#' + containerId})
      );
    }, 100);
  });

  $('#group-container').on('hidden.bs.tab', 'ul.nav-tabs li a', function(e) {
    var containerId = $(e.target).attr('href');
    Webfield.ui.spinner(containerId, {inline: true});
  });

  Webfield.ui.searchResults(
    oralDecisions,
    _.assign({}, paperDisplayOptions, {showTags: false, container: '#accepted-oral-papers'})
  );

  $('#notes > .spinner-container').remove();
  $('.tabs-container').show();

}

// Go!
main();
