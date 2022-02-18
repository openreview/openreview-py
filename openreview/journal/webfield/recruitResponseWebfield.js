// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var VENUE_ID = '';
var HEADER = {};

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#invitation-container', VENUE_ID);  // required

  Webfield.ui.venueHeader(HEADER);

  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(VENUE_ID);
  }

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
      $response.append('<div><h3 style="line-height:normal;">' + message + '</h3></div>');
      var email = args.user.indexOf('@') > -1 ? '(<strong>' + args.user + '</strong>)' : '';

      $response.append([
        '<div>',
          '<h4>Please complete the following steps now:</h4>',
          '<ol>',
            '<li><p>Log in to your OpenReview account. If you do not already have an account, you can sign up <a style="font-weight:bold;" href="/signup">here</a>.</p></li>',
            '<li><p>Ensure that the email address ' + email + ' that received this invitation is linked to your <a style="font-weight:bold;" href="/profile/edit">profile page</a> and has been confirmed.</p></li>',
            '<li><p>Complete your pending <a style="font-weight:bold;" href="/tasks">tasks</a> (if any) for ' + HEADER.short + '.</p></li>',
          '</ol>',
        '</div>',
      ].join('\n'));
    } else if (declined) {
      var message = 'You have declined the invitation from ' + HEADER.title + '.';
      $response.append('<div><h3 style="line-height:normal;">' + message + '</h3></div>');
    }
  }

  Webfield.ui.done();
}

// Go!
main();
