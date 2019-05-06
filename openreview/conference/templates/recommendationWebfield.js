// ------------------------------------
// Recommendation Interface
// ------------------------------------

var CONFERENCE_ID = '';
var HEADER = {};
var BLIND_SUBMISSION_ID = '';
var SUBJECT_AREAS = '';

var AREACHAIR_WILDCARD = CONFERENCE_ID + '/Paper.*/Area_Chair.*';

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.header(HEADER.title, HEADER.instructions);

  Webfield.ui.spinner('#notes', { inline: true });

  load().then(renderContent).then(Webfield.ui.done);
}


// Perform all the required API calls
function load() {
  return Webfield.get('/groups', {
    member: user.id, regex: AREACHAIR_WILDCARD
  }).then(function(result) {
    var noteNumbers = getPaperNumbersFromGroups(result.groups);

    var notesP;
    if (noteNumbers.length) {
      var noteNumbersStr = noteNumbers.join(',');

      notesP = Webfield.getAll('/notes', {
        invitation: BLIND_SUBMISSION_ID, number: noteNumbersStr, details: 'tags'
      }).then(function(allNotes) {
        return allNotes.map(function(note) {
          note.details.tags = note.details.tags.filter(function(tag) {
            return tag.tauthor;
          });
          return note;
        });
      });
    } else {
      notesP = $.Deferred().resolve([]);
    }

    var tagInvitationsP = Webfield.getAll('/invitations', {
      regex: CONFERENCE_ID + '/Paper.*/-/Recommendation', tags: true, invitee: true
    });

    return $.when(notesP, tagInvitationsP);
  });
}


// Util functions
function getPaperNumbersFromGroups(groups) {
  return _.filter(_.map(groups, function(group) {
    return getNumberFromGroup(group.id, 'Paper');
  }), _.isInteger);
}

function getNumberFromGroup(groupId, name) {
  var tokens = groupId.split('/');
  paper = _.find(tokens, function(token) { return token.startsWith(name); });
  if (paper) {
    return parseInt(paper.replace(name, ''));
  } else {
    return null;
  }
}


// Display the recommend interface populated with loaded data
function renderContent(notes, tagInvitations) {

  // Nothing to dispay
  if (!notes.length) {
    $('#notes').empty();
    $('#notes').append('<p class="empty-message">You have no assigned papers at this time.</p>');
    return;
  }

  // Set up tabs
  var sections = [{
    heading: 'Your Assigned Papers',
    id: 'your-assigned-submissions',
  }];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });

  // Your Assigned Papers tab
  var submissionListOptions = {
    pdfLink: true,
    showContents: true,
    showTags: true,
    tagInvitations: tagInvitations,
    container: '#your-assigned-submissions'
  };

  Webfield.ui.submissionList(notes, {
    heading: null,
    container: submissionListOptions.container,
    search: {
      enabled: true,
      localSearch: true,
      subjectAreas: SUBJECT_AREAS,
      subjectAreaDropdown: 'basic',
      onResults: function(searchResults) {
        Webfield.ui.searchResults(searchResults, submissionListOptions);
        Webfield.disableAutoLoading();
      },
      onReset: function() {
        Webfield.ui.searchResults(notes, submissionListOptions);
      }
    },
    displayOptions: submissionListOptions,
    fadeIn: false
  });

  $('#notes > .spinner-container').remove();
  $('#notes .tabs-container').show();

}

// Go!
main();
