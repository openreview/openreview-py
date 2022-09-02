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
    tabs: [
      'Your Consoles',
      'Accepted Papers',
      'Under Review Submissions',
      'All Submissions',
      'Outstanding Certification',
      'Featured Certification',
      'Expert Reviewer Certification',
      'Reproducibility Certification',
      'Survey Certification'
    ],
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

  var acceptedNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': VENUE_ID,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true,
    sort: 'tmdate:desc'
  });

  var featuredAcceptedNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': VENUE_ID,
    'content.certifications': 'Featured Certification',
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true,
    sort: 'tmdate:desc'
  });

  var reproducibilityAcceptedNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': VENUE_ID,
    'content.certifications': 'Reproducibility Certification',
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true,
    sort: 'tmdate:desc'
  });

  var surveyAcceptedNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    'content.venueid': VENUE_ID,
    'content.certifications': 'Survey Certification',
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

  var allNotesP = Webfield2.api.getSubmissions(SUBMISSION_ID, {
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var userGroupsP = $.Deferred().resolve([]);
  if (user && !_.startsWith(user.id, 'guest_')) {
    userGroupsP = Webfield2.getAll('/groups', { prefix: VENUE_ID + '/.*', member: user.id, web: true });
  }

  return $.when(acceptedNotesP, featuredAcceptedNotesP, reproducibilityAcceptedNotesP, surveyAcceptedNotesP, underReviewNotesP, allNotesP, userGroupsP);
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
function renderContent(acceptedResponse, featuredResponse, reproducibilityResponse, surveyResponse, underReviewResponse, allResponse, userGroups) {

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

  Webfield2.ui.renderSubmissionList('#accepted-papers', SUBMISSION_ID, acceptedResponse.notes, acceptedResponse.count,
  Object.assign({}, options, { query: { 'content.venueid': VENUE_ID }}));

  Webfield2.ui.renderSubmissionList('#under-review-submissions', SUBMISSION_ID, underReviewResponse.notes, underReviewResponse.count,
  Object.assign({}, options, { query: {'content.venueid': UNDER_REVIEW_ID } } ));

  Webfield2.ui.renderSubmissionList('#all-submissions', SUBMISSION_ID, allResponse.notes, allResponse.count, options);

  Webfield2.ui.renderSubmissionList('#outstanding-certification', SUBMISSION_ID, [], 0, options);

  Webfield2.ui.renderSubmissionList('#featured-certification', SUBMISSION_ID, featuredResponse.notes, featuredResponse.count,
  Object.assign({}, options, { query: { 'content.venueid': VENUE_ID, 'content.certifications': 'Featured Certification' }}));

  Webfield2.ui.renderSubmissionList('#expert-reviewer-certification', SUBMISSION_ID, [], 0, options);

  Webfield2.ui.renderSubmissionList('#reproducibility-certification', SUBMISSION_ID, reproducibilityResponse.notes, reproducibilityResponse.count,
  Object.assign({}, options, { query: { 'content.venueid': VENUE_ID, 'content.certifications': 'Reproducibility Certification' }}));

  Webfield2.ui.renderSubmissionList('#survey-certification', SUBMISSION_ID, surveyResponse.notes, surveyResponse.count,
  Object.assign({}, options, { query: { 'content.venueid': VENUE_ID, 'content.certifications': 'Survey Certification' }}));

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
