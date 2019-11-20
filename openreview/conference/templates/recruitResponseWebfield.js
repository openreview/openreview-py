// Constants
var CONFERENCE_ID = '';
var HEADER = {};
var REDUCED_LOAD_INVITATION_NAME = '';

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
      var message = 'Thank you for accepting the invitation!';
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
      var reduced_load_invitation_id = CONFERENCE_ID + '/-/' + REDUCED_LOAD_INVITATION_NAME;
      Webfield.get('/invitations', { regex: reduced_load_invitation_id })
      .then(function(result) {
        if (result.hasOwnProperty('invitations') && result.invitations.length) {
          invitation = result.invitations[0];
          $response.append([
            '<div class="panel">',
              '<div class="row">',
                '<strong><p>If you declined because you are looking for a reduced load, please use this <strong><a href="/invitation?id=' + reduced_load_invitation_id + '&invitation_response=Yes&user=' + args.user + '&key=' + args.key + '">LINK</a></strong> to request a load you would be comfortable reviewing.</p></strong>',
              '</div>',
            '</div>'
          ].join('\n'));
        } else {
          var message = 'You have declined the invitation.';
          $response.append('<div class="panel"><div class="row"><strong>' + message + '</strong></div></div>');
        }
      })
      .fail(function(error) {
        promptError(error ? error : 'Oops! An error occurred. Please contact info@openreview.net');
        return null;
      });
    }
  } else {
    promptError('Response parameter missing');
  }

  Webfield.ui.done();
}

// Go!
main();
