// Constants
var CONFERENCE_ID = '';
var REVIEWERS_NAME = '';
var HEADER_TEXT = '';
var INSTRUCTIONS = '';
var SCHEDULE_HTML = '';


// Main function is the entry point to the webfield code
var main = function() {
  OpenBanner.venueHomepageLink(CONFERENCE_ID);

  renderHeader();

};

// Render functions
var renderHeader = function() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);
  Webfield.ui.header(HEADER_TEXT, INSTRUCTIONS);

  var loadingMessage = '<p class="empty-message">Loading...</p>';
  Webfield.ui.tabPanel([
    {
      heading: REVIEWERS_NAME + ' Schedule',
      id: 'areachair-schedule',
      content: SCHEDULE_HTML,
      active: true
    }
  ]);
};


main();
