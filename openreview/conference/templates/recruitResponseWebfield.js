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
      var message = 'Thank you for accepting this invitation from ' + HEADER.title;
      $response.append('<div class="panel"><div class="row"><h3 style="line-height:normal;">' + message + '</h3></div></div>');

      $response.append([
        '<div class="panel">',
          '<div class="row">',
            '<p>If you do not already have an OpenReview account, please sign up <a style="font-weight:bold;" href="/signup">here</a>.</p>',
            '<p>If you have an existing OpenReview account, please ensure that the email address that received this invitation is linked to your <a style="font-weight:bold;" href="/profile?mode=edit">profile page</a> and has been confirmed.</p>',
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
          var message = 'You have declined the invitation from ' + HEADER.title + '.';
          $response.append('<div class="panel"><div class="row"><h3 style="line-height:normal;">' + message + '</h3></div></div>');
          $response.append([
            '<div class="panel">',
              '<div class="row">',
                '<h3 style="line-height:normal;">In case you only declined because you think you cannot handle the maximum load of papers, you can reduce your load slightly. Be aware that this will decrease your overall score for an outstanding reviewer award, since all good reviews will accumulate a positive score. You can request a reduced reviewer load by clicking here: <a style="font-weight:bold;" href="/invitation?id=' + reduced_load_invitation_id + '&user=' + args.user + '&key=' + args.key + '">Request reduced load</a></h3>',
              '</div>',
            '</div>'
          ].join('\n'));
        } else {
          var message = 'You have declined the invitation from ' + HEADER.title + '.';
          $response.append('<div class="panel"><div class="row"><h3 style="line-height:normal;">' + message + '</h3></div></div>');
        }
      })
      .fail(function(error) {
        promptError(error ? error : 'Oops! An error occurred. Please contact info@openreview.net');
        return null;
      });
    }
  }

  Webfield.ui.done();
}

// Go!
main();
