// ------------------------------------
// Recommendation Interface
// ------------------------------------

var CONFERENCE_ID = '';
var HEADER = {};
var EDGE_BROWSER_PARAMS = '';

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.header(HEADER.title, HEADER.instructions);

  Webfield.ui.spinner('#notes', { inline: true });

  load().then(renderContent).then(Webfield.ui.done);
}


// Perform all the required API calls
function load() {
  return $.Deferred().resolve();
}


// Display the recommend interface populated with loaded data
function renderContent() {

  var params = EDGE_BROWSER_PARAMS.replace('{userId}', user.profile.id);
  var browseUrl = window.location.origin + '/edge/browse?' + decodeURIComponent(params);

  $('#notes').empty().append('<a href="' + browseUrl + '" target="_blank">Go to reviewers recommendation</a>');

  $.Deferred().resolve();
}

// Go!
main();
