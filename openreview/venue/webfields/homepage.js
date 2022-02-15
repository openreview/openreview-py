// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Basic venue homepage template
//
// This webfield displays the conference header (#header), the submit button (#invitation),
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var VENUE_ID = '';
var PARENT_GROUP_ID = '';
var SUBMISSION_ID = '';
var BLIND_SUBMISSION_ID = '';
var WITHDRAWN_SUBMISSION_ID = '';
var DESK_REJECTED_SUBMISSION_ID = '';
var HEADER = {};
var PUBLIC = false;
var AUTHOR_SUBMISSION_FIELD = '';

var WILDCARD_INVITATION = VENUE_ID + '/.*';
var PAGE_SIZE = 50;

var paperDisplayOptions = {
    pdfLink: true,
    replyCount: true,
    showContents: true,
    showTags: false,
    referrer: encodeURIComponent('[' + HEADER.short + '](/group?id=' + VENUE_ID + ')')
  };

// Main is the entry point to the webfield code and runs everything
function main() {
    if (args && args.referrer) {
        OpenBanner.referrerLink(args.referrer);
    } else if (PARENT_GROUP_ID.length){
        OpenBanner.venueHomepageLink(PARENT_GROUP_ID);
    }

    Webfield2.ui.setup('#group-container', VENUE_ID, {
      title: HEADER.title,
      instructions: HEADER.instructions,
      tabs: ['Your Consoles', 'All Submissions', 'Withdrawn Submissions', 'Desk Rejected Submissions'],
      referrer: args && args.referrer,
      showBanner: false
    })

    
    Webfield2.ui.renderInvitationButton('#invitation', SUBMISSION_ID, {
      onNoteCreated: function() {
        // Callback funtion to be run when a paper has successfully been submitted (required)
        promptMessage('Your submission is complete. Check your inbox for a confirmation email. ');
  
        load().then(renderContent).then(function() {
          $('.tabs-container a[href="#your-consoles"]').click();
        });
      }
    });

      load().then(renderContent).then(Webfield2.ui.done);
}

// Load makes all the API calls needed to get the data to render the page
// It returns a jQuery deferred object: https://api.jquery.com/category/deferred-object/
function load() {

  var notesP = $.Deferred().resolve([]);
  var activityNotesP = $.Deferred().resolve([]);
  var authorNotesP = $.Deferred().resolve([]);
  var userGroupsP = $.Deferred().resolve([]);
  var withdrawnNotesP = $.Deferred().resolve([]);
  var deskRejectedNotesP = $.Deferred().resolve([]);
  
  if (PUBLIC) {
    notesP = Webfield2.api.getSubmissions(BLIND_SUBMISSION_ID, {
      pageSize: PAGE_SIZE,
      details: 'replyCount,invitation,original',
      includeCount: true
    });
  
    if (WITHDRAWN_SUBMISSION_ID) {
      withdrawnNotesP = Webfield2.api.getSubmissions(WITHDRAWN_SUBMISSION_ID, {
        pageSize: PAGE_SIZE,
        details: 'replyCount,invitation,original',
        includeCount: true
      });
    }
  
    if (DESK_REJECTED_SUBMISSION_ID) {
      deskRejectedNotesP = Webfield2.api.getSubmissions(DESK_REJECTED_SUBMISSION_ID, {
        pageSize: PAGE_SIZE,
        details: 'replyCount,invitation,original',
        includeCount: true
      });
    }
  }

  if (user && !_.startsWith(user.id, 'guest_')) {
    activityNotesP = Webfield2.api.getSubmissions(WILDCARD_INVITATION, {
      pageSize: PAGE_SIZE,
      details: 'forumContent,invitation,writable'
    });
    
    userGroupsP = Webfield2.getAll('/groups', { regex: VENUE_ID + '/.*', member: user.id, web: true });

    var query = {
      pageSize: PAGE_SIZE
    };
    query[AUTHOR_SUBMISSION_FIELD] = user.profile.id;
    authorNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, query);
  }

  return $.when(notesP, userGroupsP, activityNotesP, authorNotesP, withdrawnNotesP, deskRejectedNotesP);
}

function createConsoleLinks(allGroups) {
  var uniqueGroups = _.sortBy(_.uniq(allGroups));
  var links = [];
  uniqueGroups.forEach(function(group) {
    var groupName = group.split('/').pop();
    if (groupName.slice(-1) === 's') {
      groupName = groupName.slice(0, -1);
    }
    links.push(
      [
        '<li class="note invitation-link">',
        '<a href="/group?id=' + group + '">' + groupName.replace(/_/g, ' ') + ' Console</a>',
        '</li>'
      ].join('')
    );
  });

  $('#your-consoles .submissions-list').append(links);
}

// Render functions
function renderContent(notesResponse, userGroups, activityResponse, authorResponse, withdrawnResponse, deskRejectedResponse) {

  // Your Consoles tab
  if (userGroups.length) {

    var $container = $('#your-consoles').empty();
    $container.append('<ul class="list-unstyled submissions-list">');

    var allConsoles = [];
    userGroups.forEach(function(group) {
      allConsoles.push(group.id);
    });

    // Render all console links for the user
    createConsoleLinks(allConsoles);

    $('.tabs-container a[href="#your-consoles"]').parent().show();
  } else {
    $('.tabs-container a[href="#your-consoles"]').parent().hide();
  }

  var options = {
    paperDisplayOptions: paperDisplayOptions,
    pageSize: PAGE_SIZE
  }

  if (notesResponse.count > 0) {
    Webfield2.ui.renderSubmissionList('#all-submissions', SUBMISSION_ID, notesResponse.notes, notesResponse.count, options);
  } else {
    $('.tabs-container a[href="#all-submissions"]').parent().hide();
  }

  if (withdrawnResponse.count > 0) {
    Webfield2.ui.renderSubmissionList('#withdrawn-submissions', SUBMISSION_ID, withdrawnResponse.notes, withdrawnResponse.count, options);
  } else {
    $('.tabs-container a[href="#all-submissions"]').parent().hide();
  }

  if (deskRejectedResponse.count > 0) {
    Webfield2.ui.renderSubmissionList('#desk-rejected-submissions', SUBMISSION_ID, deskRejectedResponse.notes, deskRejectedResponse.count, options);
  } else {
    $('.tabs-container a[href="#all-submissions"]').parent().hide();
  }

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();

}

// Go!
main();