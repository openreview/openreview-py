// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Venue homepage template
//
// This webfield displays the conference header (#header), the submit button (#invitation),
// and a tabbed interface for viewing various types of notes.
// ------------------------------------

// Constants
var VENUE_ID = '';
var SUBMISSION_ID = '';
var SUBMITTED_ID = '';
var UNDER_REVIEW_ID = '';
var DESK_REJECTED_ID = '';
var WITHDRAWN_ID = '';
var REJECTED_ID = '';
var HEADER = {};

var WILDCARD_INVITATION = VENUE_ID + '/.*';
var PAGE_SIZE = 50;

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true,
  showTags: false,
  referrer: encodeURIComponent('[' + HEADER.short + '](/group?id=' + VENUE_ID + ')')
};
var commentDisplayOptions = {
  pdfLink: false,
  replyCount: true,
  showContents: false,
  showParent: true
};

// Main is the entry point to the webfield code and runs everything
function main() {

  Webfield2.ui.setup('#group-container', VENUE_ID, {
    title: HEADER.title,
    instructions: HEADER.instructions,
    tabs: ['Your Consoles', 'Accepted Papers', 'Under Review', 'Submissions', 'Rejected Submissions', 'Withdrawn Submissions'],
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

  var submittedNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': SUBMITTED_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var underReviewNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': UNDER_REVIEW_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var rejectedNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': DESK_REJECTED_ID + ',' + REJECTED_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var withdrawnNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': WITHDRAWN_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var acceptedNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': VENUE_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var userGroupsP = $.Deferred().resolve([]);
  if (user && !_.startsWith(user.id, 'guest_')) {
    userGroupsP = Webfield2.getAll('/groups', { regex: VENUE_ID + '/.*', member: user.id, web: true });
  }

  return $.when(acceptedNotesP, submittedNotesP, underReviewNotesP, rejectedNotesP, withdrawnNotesP, userGroupsP);
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
function renderContent(acceptedResponse, submittedResponse, underReviewResponse, rejectedResponse, withdrawnResponse, userGroups) {

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

  var acceptedPapers = acceptedResponse.notes || [];
  var acceptedPapersCount = acceptedResponse.count || 0;

  $('#accepted-papers').empty();

  if (acceptedPapersCount) {
    var searchResultsListOptions = _.assign({}, paperDisplayOptions, {
      container: '#accepted-papers',
      autoLoad: false
    });

    Webfield2.ui.submissionList(acceptedPapers, {
      heading: null,
      container: '#accepted-papers',
      search: {
        enabled: true,
        localSearch: false,
        invitation: SUBMISSION_ID,
        onResults: function(searchResults) {
          Webfield2.ui.searchResults(searchResults, searchResultsListOptions);
        },
        onReset: function() {
          Webfield2.ui.searchResults(notes, searchResultsListOptions);
          $('#accepted-papers').append(view.paginationLinks(acceptedPapersCount, PAGE_SIZE, 1));
        }
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: acceptedPapersCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield2.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': CONFERENCE_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#accepted-papers"]').parent().hide();
  }

  var underReviewSubmissions = underReviewResponse.notes || [];
  var underReviewCount = underReviewResponse.count || 0;

  $('#under-review').empty();

  if (underReviewCount) {
    var searchResultsListOptions = _.assign({}, paperDisplayOptions, {
      container: '#under-review',
      autoLoad: false
    });

    Webfield2.ui.submissionList(underReviewSubmissions, {
      heading: null,
      container: '#under-review',
      search: {
        enabled: true,
        localSearch: false,
        invitation: SUBMISSION_ID,
        onResults: function(searchResults) {
          Webfield2.ui.searchResults(searchResults, searchResultsListOptions);
        },
        onReset: function() {
          Webfield2.ui.searchResults(notes, searchResultsListOptions);
          $('#under-review-submissions').append(view.paginationLinks(underReviewCount, PAGE_SIZE, 1));
        }
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: underReviewCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield2.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': UNDER_REVIEW_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#under-review"]').parent().hide();
  }

  var submissionNotesCount = submittedResponse.count || 0;
  if (submissionNotesCount) {
    $('#submissions').empty();

    var notes = submittedResponse.notes || [];
    Webfield2.ui.submissionList(notes, {
      heading: null,
      container: '#submissions',
      search: {
        enabled: false
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: submissionNotesCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield2.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': SUBMITTED_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#submissions"]').parent().hide();
  }

  var rejectedNotesCount = rejectedResponse.count || 0;
  if (rejectedNotesCount) {
    $('#rejected-submissions').empty();

    var rejectedNotesArray = rejectedResponse.notes || [];
    Webfield2.ui.submissionList(rejectedNotesArray, {
      heading: null,
      container: '#rejected-submissions',
      search: {
        enabled: false
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: rejectedNotesCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield2.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': REJECTED_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#rejected-submissions"]').parent().hide();
  }

  var withDrawnNotesCount = withdrawnResponse.count || 0;
  if (withDrawnNotesCount) {
    $('#withdrawn-submissions').empty();

    var withdrawnNotesArray = withdrawnResponse.notes || [];
    Webfield2.ui.submissionList(withdrawnNotesArray, {
      heading: null,
      container: '#withdrawn-submissions',
      search: {
        enabled: false
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: withDrawnNotesCount,
      pageSize: PAGE_SIZE,
      onPageClick: function(offset) {
        return Webfield2.api.getSubmissions(SUBMISSION_ID, {
          'content.venueid': WITHDRAWN_ID,
          details: 'replyCount',
          pageSize: PAGE_SIZE,
          offset: offset
        });
      },
      fadeIn: false
    });
  } else {
    $('.tabs-container a[href="#withdrawn-submissions"]').parent().hide();
  }

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
