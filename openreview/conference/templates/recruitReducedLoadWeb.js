// Constants
var CONFERENCE_ID = '';
var HEADER = {};

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.venueHeader(HEADER);

  OpenBanner.venueHomepageLink(CONFERENCE_ID);

  Webfield.ui.done();
}

// Go!
main();
