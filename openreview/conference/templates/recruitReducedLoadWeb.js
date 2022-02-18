// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var CONFERENCE_ID = '';
var HEADER = {};

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.venueHeader(HEADER);

  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID);
  }

  render();
}

function render() {
  var $response = $('#notes');
  $response.empty();

  if (note && note.content.response) {
    var accepted = (note.content.response === 'Yes');
    var declined = (note.content.response === 'No');

    if (accepted) {
      // Display response text
      var message = 'Thank you for accepting this invitation from ' + HEADER.title;
      $response.append('<div><strong>' + message + '</strong></div>');
      $response.append([
        '<div>',
          '<p>If you do not already have an OpenReview account, please sign up <a href="/signup" target="_blank" rel="nofollow">here</a>.</p>',
          '<p>If you have an existing OpenReview account, please ensure that the email address that received this invitation is linked to your <a href="/profile/edit" target="_blank" rel="nofollow">profile page</a> and has been confirmed.</p>',
        '</div>',
      ].join('\n'));
    } else if (declined) {
      // Get invitation to request max load
      var message = 'You have declined the invitation from ' + HEADER.title + '.';
      $response.append('<div><strong>' + message + '</strong></div>');
    }
  }

  Webfield.ui.done();
}

// Go!
main();
