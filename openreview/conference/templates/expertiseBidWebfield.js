// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Add EXPERTISE SELECTION Interface
// ------------------------------------

var CONFERENCE_ID = '';
var HEADER = {};
var SHORT_PHRASE = '';
var BLIND_SUBMISSION_ID = '';
var SUBMISSION_ID = '';
var EXPERTISE_BID_ID = '';
var EXPERTISE_SUBMISSION_ID = 'OpenReview.net/Archive/-/Direct_Upload';

var BUFFER = 1000 * 60 * 30;  // 30 minutes

var bidOptionLabel = invitation.reply.content.label['value-radio'][0];
var bidOptionId = bidOptionLabel.toLowerCase()
// Main is the entry point to the webfield code and runs everything
function main() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID);
  }

  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.header(HEADER.title, HEADER.instructions);

  renderSubmissionButton(EXPERTISE_SUBMISSION_ID);

  Webfield.ui.spinner('#notes', { inline: true });

  load().then(renderContent).then(Webfield.ui.done);
}

// Perform all the required API calls
function renderSubmissionButton(INVITATION_ID) {
  Webfield.api.getSubmissionInvitation(INVITATION_ID, {deadlineBuffer: BUFFER})
    .then(function(invitation) {
      Webfield.ui.submissionButton(invitation, user, {
        onNoteCreated: function() {
          // Callback funtion to be run when a paper has successfully been submitted (required)
          promptMessage('Your submission is complete.');
          load().then(renderContent).then(function() {
            $('.tabs-container a[href="#allPapers"]').click();
          });
        }
      });
    });
}

function load() {

  var authoredNotesP = $.Deferred().resolve([]);
  var edgesMapP = $.Deferred().resolve({});

  if (user && user.profile && user.profile.id) {
    authoredNotesP = Webfield.getAll('/notes', {
      'content.authorids': user.profile.id,
      details: 'invitation',
      sort: 'cdate'
    })
    .then(function(notes){
      return notes.filter(function(note){
        return note.readers.includes('everyone');
      });
    });

    edgesMapP = Webfield.getAll('/edges', {
      invitation: EXPERTISE_BID_ID,
      tail : user.profile.id
    })
    .then(function(edges) {
      if (!edges || !edges.length) {
        return {}
      }

      return edges.reduce(function(noteMap, edge) {
        // Only include the users bids in the map
        noteMap[edge.head] = edge;
        return noteMap;
      }, {});
    });
  } else {
    // Log exception to GA if user object is empty, since only authenticated users
    // should be able to access the invitation. Don't log actual cookie value for safety.
    window.gtag('event', 'exception', {
      description: 'JavaScript Error: Missing user in expertise bid webfield. Invitation: ' + INVITATION_ID + ', AuthCookie: ' + !!getCookie('openreview.accessToken'),
      fatal: true,
    });
  }

  return $.when(authoredNotesP, edgesMapP);
}

function getCookie(name) {
  return (name = (document.cookie + ';').match(new RegExp(name + '=.*;'))) && name[0].split(/=|;/)[1];
}

// Display the expertise selection interface populated with loaded data
function renderContent(authoredNotes, edgesMap) {
  addEdgesToNotes(authoredNotes, edgesMap);

  var activeTab = 0;
  var sections;
  var binnedNotes;

  var paperDisplayOptions = {
    pdfLink: true,
    replyCount: true,
    showContents: true,
    showTags: false,
    showEdges: true,
    edgeInvitations: [invitation] // Expertise Selection invitation automatically available here
  };

  $('#invitation-container').on('shown.bs.tab', 'ul.nav-tabs li a', function(e) {
    activeTab = $(e.target).data('tabIndex');
    var containerId = sections[activeTab].id;

    if (containerId !== 'allPapers') {
      setTimeout(function() {
        Webfield.ui.submissionList(binnedNotes[containerId], {
          heading: null,
          container: '#' + containerId,
          search: { enabled: false },
          displayOptions: paperDisplayOptions,
          fadeIn: false
        });
      }, 100);
    }
  });

  $('#invitation-container').on('hidden.bs.tab', 'ul.nav-tabs li a', function(e) {
    var containerId = $(e.target).attr('href');
    if (containerId !== '#allPapers') {
      Webfield.ui.spinner(containerId, {inline: true});
    }
  });

  $('#invitation-container').on('bidUpdated', '.tag-widget', function(e, edgeObj) {
    var updatedNote = _.find(authoredNotes, ['id', edgeObj.head]);
    if (!updatedNote) {
      return;
    }
    var prevEdgeIndex = _.findIndex(updatedNote.details.edges, ['invitation', EXPERTISE_BID_ID]);
    var prevVal = prevEdgeIndex !== -1 ?
      updatedNote.details.edges[prevEdgeIndex].label :
      'No Selection';

    if (edgeObj.ddate) {
      edgeObj.label = 'No Selection';
    }
    updatedNote.details.edges[prevEdgeIndex] = edgeObj;

    var labelToContainerId = {
      'No Selection': 'noSelection'
    };
    labelToContainerId[bidOptionLabel] = bidOptionId;

    var previousNoteList = binnedNotes[labelToContainerId[prevVal]];
    var currentNoteList = binnedNotes[labelToContainerId[edgeObj.label]];

    var currentIndex = _.findIndex(previousNoteList, ['id', edgeObj.head]);
    if (currentIndex !== -1) {
      var currentNote = previousNoteList[currentIndex];
      currentNote.details.edges = [edgeObj]; // Assumes notes will have only 1 type of edge
      previousNoteList.splice(currentIndex, 1);
      currentNoteList.push(currentNote);
    } else {
      console.warn('Note not found!');
    }

    // If the current tab is not the All Papers tab remove the note from the DOM and
    // update the state of edge widget in the All Papers tab
    if (activeTab) {
      var $elem = $(e.target).closest('.note');
      $elem.fadeOut('normal', function() {
        $elem.remove();

        var $container = $('#' + labelToContainerId[prevVal] + ' .submissions-list');
        if (!$container.children().length) {
          $container.append('<li><p class="empty-message">No papers to display at this time</p></li>');
        }
      });

      var $noteToChange = $('#allPapers .submissions-list .note[data-id="' + updatedNote.id + '"]');
      $noteToChange.find('label[data-value="' + prevVal + '"]').removeClass('active')
        .children('input').prop('checked', false);
      $noteToChange.find('label[data-value="' + edgeObj.label + '"]').button('toggle');
    }

    updateCounts();
  });

  function updateNotes(notes) {
    // Sort notes into bins by bid
    binnedNotes = {
      noSelection: []
    }
    binnedNotes[bidOptionId] = [];

    var bids, n;
    for (var i = 0; i < notes.length; i++) {
      n = notes[i];
      bids = _.filter(n.details.edges, function(t) {
        return t.invitation === EXPERTISE_BID_ID;
      });

      if (bids.length) {
        if (bids[0].label === bidOptionLabel) {
          binnedNotes[bidOptionId].push(n);
        } else {
          binnedNotes.noSelection.push(n);
        }
      } else {
        binnedNotes.noSelection.push(n);
      }
    }

    var loadingContent = Handlebars.templates.spinner({ extraClasses: 'spinner-inline' });
    sections = [
      {
        heading: 'All My Papers  <span class="glyphicon glyphicon-search"></span>',
        id: 'allPapers',
        content: null
      }
    ];
    if (bidOptionLabel == 'Exclude') {
      sections.push({
        heading: 'My Selected Expertise',
        headingCount: binnedNotes.noSelection.length,
        id: 'noSelection',
        content: loadingContent
      })
      sections.push({
        heading: bidOptionLabel + 'd Papers',
        headingCount: binnedNotes[bidOptionId].length,
        id: bidOptionId,
        content: loadingContent
      });      
    } else {
      sections.push({
        heading: 'My Selected Expertise',
        headingCount: binnedNotes[bidOptionId].length,
        id: bidOptionId,
        content: loadingContent
      })      
    }

    sections[activeTab].active = true;

    $('#notes .tabs-container').remove();

    Webfield.ui.tabPanel(sections, {
      container: '#notes',
      hidden: true
    });

    // Render the contents of the All Papers tab
    var searchResultsOptions = _.assign({}, paperDisplayOptions, { container: '#allPapers' });
    Webfield.ui.submissionList(notes, {
      heading: null,
      container: '#allPapers',
      search: {
        enabled: true,
        localSearch: true,
        sort: false,
        onResults: function(searchResults) {
          Webfield.ui.searchResults(searchResults, searchResultsOptions);
        },
        onReset: function() {
          Webfield.ui.searchResults(notes, searchResultsOptions);
        },
      },
      displayOptions: paperDisplayOptions,
      //pageSize: 50,
      fadeIn: false
    });

    $('#notes > .spinner-container').remove();
    $('#notes .tabs-container').show();
  }

  function updateCounts() {
    var containers = [
      'noSelection']
    containers.push(bidOptionId);
    var totalCount = 0;

    containers.forEach(function(containerId) {
      var $tab = $('ul.nav-tabs li a[href="#' + containerId + '"]');
      var numPapers = binnedNotes[containerId].length;

      $tab.find('span.badge').remove();
      if (numPapers) {
        $tab.append('<span class="badge">' + numPapers + '</span>');
      }

      if (containerId != 'noSelection') {
        totalCount += numPapers;
      }
    });
  }
  updateNotes(authoredNotes);

  // Mark task a complete
  if (bidOptionLabel == 'Exclude' && user && user.profile && user.profile.id && _.isEmpty(edgesMap)) {
    Webfield.post('/edges', {
      invitation: EXPERTISE_BID_ID,
      readers: [CONFERENCE_ID, user.profile.id],
      writers: [CONFERENCE_ID, user.profile.id],
      signatures: [user.profile.id],
      head: 'xf0zSBd2iufMg', //OpenReview paper
      tail: user.profile.id,
      label: 'Exclude'
    });
  }
}

function addEdgesToNotes(notesArray, edgesMap) {
  for (var i = 0; i < notesArray.length; i++) {
    var noteId = notesArray[i].id;
    if (edgesMap.hasOwnProperty(noteId)) {
      notesArray[i].details = {edges : [edgesMap[noteId]]};
    } else {
      notesArray[i].details = {edges : []};
    }
  }
}

// Go!
main();
