// Constants
var CONFERENCE_ID = '';
var HEADER = {};

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.venueHeader(HEADER);

  OpenBanner.venueHomepageLink(CONFERENCE_ID);

  render();
}


function render() {
  var $response = $('#notes');
  $response.empty();

  if (args.response) {
    var accepted = (args.response === 'Yes');
    var message = accepted ? 'Thank you for accepting the invitation!' : 'You have declined the invitation.';

    $response.append('<div class="panel"><div class="row"><strong>' + message + '</strong></div></div>');

    if (accepted) {
      // Display response text
      $response.append([
        '<div class="panel">',
          '<div class="row">',
            '<p>If you do not already have an OpenReview account, please sign up <a href="/signup">here</a>.</p>',
            '<p>If you have an existing OpenReview account, please ensure that the email address that received this invitation is linked to your <a href="/profile?mode=edit">profile page</a> and has been confirmed.</p>',
          '</div>',
        '</div>'
      ].join('\n'));
    }

  } else {
    promptError('Response parameter missing');
  }

  Webfield.ui.done();
}

// Go!
main();
