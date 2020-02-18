// ------------------------------------
// Add Bid Interface
// ------------------------------------

var CONFERENCE_ID = '';
var BLIND_INVITATION_ID = CONFERENCE_ID + '/-/Blind_Submission';
var ANONREVIEWER_WILDCARD = CONFERENCE_ID + '/Paper.*/AnonReviewer.*';
var PAPER_RANKING_ID = '';
var GROUP_NAME = '';

var INSTRUCTIONS = '<p class="dark">Please indicate your level of interest in reviewing \
  the submitted papers below, on a scale from "Very Low" to "Very High".</p>\
  <p class="dark"><strong>Please note:</strong></p>\
  <ul>\
    <li><strong>Conflict of interest will be taken into account at the next stage. So, please do not worry about that while bidding.</strong></li>\
    <li>Please update your Conflict of Interest details on your profile page, specifically "Emails", "Education and Career History" & "Advisors and Other Relations" fields.</li>\
  </ul>\
  <p class="dark"><strong>A few tips:</strong></p>\
  <ul>\
    <li>We expect <strong>approximately 50 bids per user</strong>. Please bid on as many papers as possible to ensure that your preferences are taken into account.</li>\
    <li>For the best bidding experience, <strong>it is recommended that you filter papers by Subject Area</strong> and search for key phrases in paper metadata using the search form.</li>\
    <li>Don\'t worry about suspected conflicts of interest during the bidding process. These will be accounted for during the paper matching process.</li>\
    <li>Default bid on each paper is \"No Bid\".</li>\
  </ul><br>'

var getNumberfromGroup = function(groupId, name) {
  var tokens = groupId.split('/');
  var paper = _.find(tokens, function(token) {
      return _.startsWith(token, name);
  });

  if (paper) {
    return parseInt(paper.replace(name, ''), 10);
  } else {
    return null;
  }
};

var getPaperNumbersfromGroups = function(groups) {
  return _.filter(_.map(groups, function(group) {
    return getNumberfromGroup(group.id, 'Paper');
  }), _.isInteger);
};

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.header(GROUP_NAME + ' Paper Ranking Console', INSTRUCTIONS);

  Webfield.ui.spinner('#notes', { inline: true });

  load().then(renderContent);
}


// Perform all the required API calls
function load() {
  var notesP = Webfield.getAll('/groups', {member: user.id, regex: ANONREVIEWER_WILDCARD})
  .then(function(groups) {
    return getPaperNumbersfromGroups(groups);
  })
  .then(function(noteNumbers) {
    var noteNumbersStr = noteNumbers.join(',');

    return Webfield.get('/notes', { invitation: BLIND_INVITATION_ID, number: noteNumbersStr, details: 'tags' })
      .then(function(result) {
        return result.notes;
      });
  });

  var tagInvitationsP = Webfield.getAll('/invitations', {id: PAPER_RANKING_ID, type: 'tags'}).then(function(invitations) {
    return invitations.filter(function(invitation) {
      return invitation.invitees.length;
    });
  });

  return $.when(notesP, tagInvitationsP);
}


// Display the bid interface populated with loaded data
function renderContent(notes, tagInvitations) {

  var paperDisplayOptions = {
    pdfLink: true,
    replyCount: true,
    showContents: true,
    showTags: true,
    tagInvitations: tagInvitations
  };

  var sections = [
    {
      heading: 'Assigned Papers',
      id: 'allPapers',
      content: null
    }
  ];
  sections[0].active = true;

  $('#notes .tabs-container').remove();

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });

  // Render the contents of the All Papers tab
  Webfield.ui.submissionList(notes, {
    heading: null,
    container: '#allPapers',
    displayOptions: paperDisplayOptions,
    search: {
      enabled: false
    },
    pageSize: 50,
    fadeIn: false
  });

  $('#notes > .spinner-container').remove();
  $('#notes .tabs-container').show();

  Webfield.ui.done();
}


// Go!
main();
