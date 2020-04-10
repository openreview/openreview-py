// ------------------------------------
// Add Bid Interface
// ------------------------------------

var CONFERENCE_ID = '';
var BLIND_INVITATION_ID = CONFERENCE_ID + '/-/Blind_Submission';
var WILDCARD = '';
var PAPER_RANKING_ID = '';
var GROUP_NAME = '';

var INSTRUCTIONS = '<p class="dark">Please select how each paper ranks among the entire batch of papers you are reviewing (1=best).</p>\
<br>'

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
  var notesP = Webfield.getAll('/groups', {member: user.id, regex: WILDCARD})
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

  var paperRankingInvitationP = Webfield.getAll('/invitations', {id: PAPER_RANKING_ID, type: 'tags'}).then(function(invitations) {
    var foundInvitations = invitations.filter(function(invitation) {
      return invitation.invitees.length;
    });

    if (foundInvitations.length) {
      return foundInvitations[0];
    } else {
      promptError('Invitation not found');
    }
  });

  return $.when(notesP, paperRankingInvitationP);
}


// Display the bid interface populated with loaded data
function renderContent(notes, paperRankingInvitation) {

  paperRankingInvitation.reply.content.tag['value-dropdown'] = paperRankingInvitation.reply.content.tag['value-dropdown'].slice(0, notes.length);

  var paperDisplayOptions = {
    pdfLink: true,
    replyCount: true,
    showContents: true,
    showTags: true,
    tagInvitations: [paperRankingInvitation],
    referrer: encodeURIComponent('[Paper Ranking](/invitation?id=' + PAPER_RANKING_ID + ')')
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
