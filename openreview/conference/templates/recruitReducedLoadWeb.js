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
    var declined = (args.response === 'No');

    if (accepted) {
      // Display response text
      var message = 'Thank you for accepting this invitation from ' + HEADER.title;
      $response.append('<div class="panel"><div class="row"><strong>' + message + '</strong></div></div>');

      $response.append([
        '<div class="panel">',
          '<div class="row">',
            '<p>If you do not already have an OpenReview account, please sign up <a href="/signup">here</a>.</p>',
            '<p>If you have an existing OpenReview account, please ensure that the email address that received this invitation is linked to your <a href="/profile?mode=edit">profile page</a> and has been confirmed.</p>',
          '</div>',
        '</div>'
      ].join('\n'));
    } else if (declined) {
      // Get invitation to request max load
      var message = 'You have declined the invitation from ' + HEADER.title + '.';
      $response.append('<div class="panel"><div class="row"><strong>' + message + '</strong></div></div>');
    }
  } else {
    promptError('Response parameter missing');
  }

  Webfield.ui.done();
}

// Go!
main();
