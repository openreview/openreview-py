// webfield_template
// Remove line above if you don't want this page to be overwriten

var GROUP_ID = '';
var PARENT_GROUP_ID = '';
var HEADER = {
  title: '',
  description: ''
};
var VENUE_LINKS = [];

Webfield.ui.setup('#group-container', GROUP_ID);

Webfield.ui.header(HEADER.title, HEADER.description, { underline: true });

Webfield.ui.linksList(VENUE_LINKS);

if (args && args.referrer) {
  OpenBanner.referrerLink(args.referrer);
} else if (PARENT_GROUP_ID.length){
  OpenBanner.venueHomepageLink(PARENT_GROUP_ID);
}

