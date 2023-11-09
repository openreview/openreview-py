// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Recommendation Interface
// ------------------------------------

var CONFERENCE_ID = '';
var SHORT_PHRASE = '';
var TOTAL_RECOMMENDATIONS = '';
var HEADER = {
    'title': SHORT_PHRASE + ' Reviewer Recommendation',
    'instructions': '<p class="dark">Recommend a ranked list of reviewers for each of your assigned papers.</p>\
        <p class="dark"><strong>Instructions:</strong></p>\
        <ul>\
            <li>For each of your assigned papers, please select ' + TOTAL_RECOMMENDATIONS + ' reviewers to recommend.</li>\
            <li>Recommendations should each be assigned a number from 10 to 1, with 10 being the strongest recommendation and 1 the weakest.</li>\
            <li>Reviewers who have conflicts with the selected paper are not shown.</li>\
            <li>The list of reviewers for a given paper can be sorted by different parameters such as affinity score or bid. In addition, the search box can be used to search for a specific reviewer by name or institution.</li>\
            <li>To get started click the button below.</li>\
        </ul>\
        <br>'
};
var EDGE_BROWSER_PARAMS = '';

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
      '<a href="' + browseUrl + '" class="btn btn-lg btn-primary" >Recommend Reviewers</a>' +
    '</p>'
  );

  return $.Deferred().resolve();
}

// Go!
main();
