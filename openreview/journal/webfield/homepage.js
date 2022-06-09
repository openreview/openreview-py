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
var SUBMITTED_STATUS = '';
var UNDER_REVIEW_STATUS = '';
var DESK_REJECTED_STATUS = '';
var WITHDRAWN_STATUS = '';
var REJECTED_STATUS = '';
var ACCEPTED_STATUS = '';
var RETRACTED_STATUS = '';
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

  var acceptedNotesP = Webfield2.api.get(VENUE_ID, {
    'content.venue': ACCEPTED_STATUS,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var featuredAcceptedNotesP = Webfield2.api.getSubmissions(VENUE_ID, {
    'content.venue': ACCEPTED_STATUS,
    'content.certifications': 'Featured Certification',
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var reproducibilityAcceptedNotesP = Webfield2.api.getSubmissions(VENUE_ID, {
    'content.venue': ACCEPTED_STATUS,
    'content.certifications': 'Reproducibility Certification',
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var surveyAcceptedNotesP = Webfield2.api.getSubmissions(VENUE_ID, {
    'content.venue': ACCEPTED_STATUS,
    'content.certifications': 'Survey Certification',
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var underReviewNotesP = Webfield2.api.getSubmissions(VENUE_ID, {
    'content.venue': UNDER_REVIEW_STATUS,
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var allNotesP = Webfield2.api.getSubmissions(VENUE_ID, {
    pageSize: PAGE_SIZE,
    details: 'replyCount',
    includeCount: true
  });

  var userGroupsP = $.Deferred().resolve([]);
  if (user && !_.startsWith(user.id, 'guest_')) {
    userGroupsP = Webfield2.getAll('/groups', { regex: VENUE_ID + '/.*', member: user.id, web: true });
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

  Webfield2.ui.renderSubmissionList('#accepted-papers', VENUE_ID, acceptedResponse.notes, acceptedResponse.count,
  Object.assign({}, options, { query: { 'content.venue': ACCEPTED_STATUS, }}));

  Webfield2.ui.renderSubmissionList('#under-review-submissions', VENUE_ID, underReviewResponse.notes, underReviewResponse.count,
  Object.assign({}, options, { query: {'content.venue': UNDER_REVIEW_STATUS } } ));

  Webfield2.ui.renderSubmissionList('#all-submissions', VENUE_ID, allResponse.notes, allResponse.count, options);

  Webfield2.ui.renderSubmissionList('#outstanding-certification', VENUE_ID, [], 0, options);

  Webfield2.ui.renderSubmissionList('#featured-certification', VENUE_ID, featuredResponse.notes, featuredResponse.count,
  Object.assign({}, options, { query: { 'content.venue': ACCEPTED_STATUS, 'content.certifications': 'Featured Certification' }}));

  Webfield2.ui.renderSubmissionList('#expert-reviewer-certification', VENUE_ID, [], 0, options);

  Webfield2.ui.renderSubmissionList('#reproducibility-certification', VENUE_ID, reproducibilityResponse.notes, reproducibilityResponse.count,
  Object.assign({}, options, { query: { 'content.venue': ACCEPTED_STATUS, 'content.certifications': 'Reproducibility Certification' }}));

  Webfield2.ui.renderSubmissionList('#survey-certification', VENUE_ID, surveyResponse.notes, surveyResponse.count,
  Object.assign({}, options, { query: { 'content.venue': ACCEPTED_STATUS, 'content.certifications': 'Survey Certification' }}));

  $('#notes .spinner-container').remove();
  $('.tabs-container').show();
}

// Go!
main();
