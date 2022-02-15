// webfield_template
// Remove line above if you don't want this page to be overwriten

var GROUP_ID = '';
var PARENT_GROUP_ID = '';
var HEADER = {
  title: '',
  instructions: ''
};
var VENUE_LINKS = [];

Webfield2.ui.setup('#group-container', GROUP_ID, {
  title: HEADER.title,
  instructions: HEADER.instructions
});

Webfield2.ui.linksList(VENUE_LINKS);

if (args && args.referrer) {
  OpenBanner.referrerLink(args.referrer);
} else if (PARENT_GROUP_ID.length){
  OpenBanner.venueHomepageLink(PARENT_GROUP_ID);
}