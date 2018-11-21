// Constants
var CONFERENCE_ID = '';
var REVIEWERS_NAME = '';
var HEADER_TEXT = '';
var INSTRUCTIONS = '';
var SCHEDULE_HTML = '';


// Main function is the entry point to the webfield code
var main = function() {
  Webfield.ui.setup('#group-container', CONFERENCE_ID);

  Webfield.ui.header(HEADER_TEXT, INSTRUCTIONS);

  OpenBanner.venueHomepageLink(CONFERENCE_ID);

  render();
};


// Render functions
var render = function() {

  var sections = [
    {
      heading: REVIEWERS_NAME + ' Schedule',
      id: 'areachair-schedule',
      content: SCHEDULE_HTML,
      active: true
    }
  ];
  Webfield.ui.tabPanel(sections, {
    container: '#notes',
  });

};


main();
