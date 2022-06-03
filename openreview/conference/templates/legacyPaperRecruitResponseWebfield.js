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
    var userEmail = note.content.user;
    var key = note.content.key;

    if (accepted) {
      // Display response text
      var message = 'Thank you for accepting this invitation from ' + HEADER.title + '.';
      $response.append('<div><h3 style="line-height:normal;">' + message + '</h3></div>');
      var email = userEmail.indexOf('@') > -1 ? '(<strong>' + userEmail + '</strong>)' : '';

      $response.append([
        '<div>',
          '<h4>Please complete the following steps now:</h4>',
          '<ol>',
            '<li><p>Log in to your OpenReview account. If you do not already have an account, you can sign up <a style="font-weight:bold;" href="/signup" target="_blank" rel="nofollow">here</a>.</p></li>',
            '<li><p>Ensure that the email address ' + email + ' that received this invitation is linked to your <a style="font-weight:bold;" href="/profile/edit" target="_blank" rel="nofollow">profile page</a> and has been confirmed.</p></li>',
            '<li><p>Complete your pending <a style="font-weight:bold;" href="/tasks" target="_blank" rel="nofollow">tasks</a> (if any) for ' + HEADER.subtitle + '.</p></li>',
          '</ol>',
        '</div>',
      ].join('\n'));
    } else if (declined) {
      var message = 'You have declined the invitation from ' + HEADER.title + '.';
      $response.append('<div><h3 style="line-height:normal;">' + message + '</h3></div>');
      $response.append([
        '<form>',
          '<div class="form-group">',
            '<h5 style="line-height:normal;">Please tell us why you are declining the invitation:</h5>',
            '<textarea id="comment" class="form-control" style="width: 50%"></textarea>',
          '</div>',
          '<button type="submit" class="btn btn-sm btn-submit">Submit</button>',
        '</form>'
      ].join('\n'));
      $('#notes').on('click', 'button.btn.btn-submit', function(e) {
        var comment = $('#comment').val();
        if (comment && comment.length) {
          note.content.comment = comment;
          Webfield.post('/notes', note)
          .then(function(result) {
            $('#notes').empty().append('<div><h5 style="line-height:normal;">Thank you for your response.</h5></div>');
         });
        }
        return false;
      });
    }
  }

  Webfield.ui.done();
}

// Go!
main();
