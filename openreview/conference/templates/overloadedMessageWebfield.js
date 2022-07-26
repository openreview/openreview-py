// ------------------------------------
// Static message template
// ------------------------------------

// Constants
var CONFERENCE_ID = '';
var PARENT_GROUP_ID = '';

function main() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else if (PARENT_GROUP_ID.length){
    OpenBanner.venueHomepageLink(PARENT_GROUP_ID);
  }

  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  renderConferenceHeader();

  renderMessage();

  Webfield.ui.done();
}

function renderConferenceHeader() {
  Webfield.ui.venueHeader(HEADER);

  Webfield.ui.spinner('#notes', { inline: true });
}

function renderMessage() {
  $('#notes').empty().append(
    '<div class="alert alert-warning"><span class="glyphicon glyphicon-info-sign"></span> OpenReview is currently experiencing high demand. Please check back soon.</div>'
  );
}

main();
