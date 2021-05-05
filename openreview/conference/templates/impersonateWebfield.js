// webfield_template
// Remove line above if you don't want this page to be overwriten

// Constants
var CONFERENCE_ID = '';
var PARENT_GROUP_ID = '';
var HEADER = {};


// Main is the entry point to the webfield code and runs everything
function main() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else if (PARENT_GROUP_ID.length){
    OpenBanner.venueHomepageLink(PARENT_GROUP_ID);
  }

  Webfield.ui.setup('#group-container', CONFERENCE_ID);  // required

  renderHeader();

  renderContent();

  Webfield.ui.done();
}

function renderHeader() {
  Webfield.ui.venueHeader(HEADER);
  $('#header .description').append(
    '<p class="dark">Enter the email address or username of the user you would like to impersonate below:</p>'
  );
}

function renderContent() {
  $('#notes').html([
    '<div class="row">',
      '<div class="col-sm-12 col-md-8 col-lg-6 col-md-offset-2 col-lg-offset-3">',
        '<form class="form-inline mb-4 mt-3">',
          '<div class="input-group mr-2" style="width: calc(100% - 128px)">',
            '<div class="input-group-addon" style="width: 34px">',
              '<span class="glyphicon glyphicon-user " aria-hidden="true"></span>',
            '</div>',
            '<input id="groupId" type="text" class="form-control " placeholder="john@example.com, ~Jane_Doe1" value="">',
          '</div>',
          '<button type="submit" class="btn" style="width: 120px">Impersonate</button>',
        '</form>',
      '</div>',
    '</div>',
  ].join(''));
}

// Go!
main();

// Event handlers
$('#group-container').on('click', 'button.btn', function(e) {
  var userId = $('#groupId').val();
  if (!userId) return false;

  Webfield.post('/impersonate', { groupId: userId })
  .then(function(result) {
    location.href = '/profile';
    return;
  })
  .fail(function(error) {
    promptError(error);
  });
  return false;
});
