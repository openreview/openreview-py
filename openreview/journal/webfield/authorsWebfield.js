var VENUE_ID = '';
var HEADER = {
    title: 'TMLR Author Console',
    instructions: 'Put instructions here'
};

// Main is the entry point to the webfield code and runs everything
function main() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(VENUE_ID);
  }

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    referrer: args && args.referrer
  })

  load().then(renderContent).then(Webfield.ui.done);
}

function load() {
  return $.Deferred().resolve();
}

function renderContent() {
  return $.Deferred().resolve();
}

// Go!
main();