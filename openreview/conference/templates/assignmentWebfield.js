// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Assignment Interface
// ------------------------------------

var CONFERENCE_ID = '';
var HEADER = {};
var EDGE_BROWSER_PARAMS = '';
var BUTTON_NAME = '';

// Main is the entry point to the webfield code and runs everything
function main() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID);
  }

  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.header(HEADER.title, HEADER.instructions);

  Webfield.ui.spinner('#notes', { inline: true });

  load().then(renderContent).then(Webfield.ui.done);
}

function load() {
  return $.Deferred().resolve();
}

function renderContent() {
  var params = EDGE_BROWSER_PARAMS.replace('{userId}', user.profile.id);
  var browseUrl = location.origin + '/edges/browse?' + params;

  $('#content').removeClass('legacy-styles');
  $('#notes').empty().append(
    '<p class="text-center">' +
      '<a href="' + browseUrl + '" class="btn btn-lg btn-primary" >' + BUTTON_NAME + '</a>' +
    '</p>'
  );

  return $.Deferred().resolve();
}

// Go!
main();
