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

  renderConferenceTabs();

  Webfield.ui.spinner('#notes', { inline: true });

  Webfield.get('/groups', {
    member: user.id, regex: AREACHAIR_WILDCARD
  })
  .then(function(result) {
    return getPaperNumbersfromGroups(result.groups);
  })
  .then(load)
  .then(renderContent)
  .then(Webfield.ui.done);
}

// Util functions
var getNumberfromGroup = function(groupId, name) {

  var tokens = groupId.split('/');
  paper = _.find(tokens, function(token) { return token.startsWith(name); });
  if (paper) {
    return parseInt(paper.replace(name, ''));
  } else {
    return null;
  }
};

var getPaperNumbersfromGroups = function(groups) {
  return _.filter(_.map(groups, function(group) {
    return getNumberfromGroup(group.id, 'Paper');
  }), _.isInteger);
};

function renderConferenceTabs() {
  var sections = [
    {
      heading: 'Your assigned papers',
      id: 'all-submissions',
    }
  ];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });
}


// Perform all the required API calls
function load(noteNumbers) {

  var notesP = $.Deferred().resolve([]);

  if (noteNumbers.length) {
    var noteNumbersStr = noteNumbers.join(',');

    notesP = Webfield.getAll('/notes', {invitation: BLIND_SUBMISSION_ID, number: noteNumbersStr, details: 'tags'}).then(function(allNotes) {
      return allNotes.map(function(note) {
        note.details.tags = note.details.tags.filter(function(tag) {
          return tag.tauthor;
        });
        return note;
      });
    });
  }

  var tagInvitationsP = Webfield.getAll('/invitations', { regex: CONFERENCE_ID + '/-/Paper.*/Recommendation', tags: true, invitee: true });

  return $.when(notesP, tagInvitationsP);
}


// Display the bid interface populated with loaded data
function renderContent(notes, tagInvitations) {

  $('#notes .tabs-container').remove();
  var sections = [
    {
      heading: 'Your assigned papers',
      id: 'all-submissions',
    }
  ];

  Webfield.ui.tabPanel(sections, {
    container: '#notes',
    hidden: true
  });

  // All Submitted Papers tab
  var submissionListOptions = {
    pdfLink: true,
    showContents: true,
    showTags: true,
    tagInvitations: tagInvitations,
    container: '#all-submissions'
  };

  $(submissionListOptions.container).empty();

  if (notes.length){
    Webfield.ui.submissionList(notes, {
      heading: null,
      container: '#all-submissions',
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

  } else {
    $('.tabs-container a[href="#all-submissions"]').parent().hide();
  }


  $('#notes > .spinner-container').remove();
  $('#notes .tabs-container').show();

  Webfield.ui.done();
}

// Go!
main();
