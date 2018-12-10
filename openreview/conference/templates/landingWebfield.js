var GROUP_ID = '';
var HEADER = {
  title: '',
  description: ''
};
var VENUE_LINKS = [];

Webfield.ui.setup('#group-container', GROUP_ID);

Webfield.ui.header(HEADER.title, HEADER.description, { underline: true });

Webfield.ui.linksList(VENUE_LINKS);

OpenBanner.welcome();
