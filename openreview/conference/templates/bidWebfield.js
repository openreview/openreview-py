// ------------------------------------
// Add Bid Interface
// ------------------------------------

var CONFERENCE_ID = '';
var HEADER = {};
var SHORT_PHRASE = '';
var BLIND_SUBMISSION_ID = '';
var SUBMISSION_ID = '';
var BID_ID = '';
var SUBJECT_AREAS = '';

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.header(HEADER.title, HEADER.instructions);

  Webfield.ui.spinner('#notes', { inline: true });

  load().then(renderContent).then(Webfield.ui.done);
}


// Perform all the required API calls
function load() {
  var notesP = Webfield.get('/notes', {
    invitation: BLIND_SUBMISSION_ID,
    noDetails: true,
    limit: 50,
    offset: 0
  }).then(function(result) { return result.notes; });

  var authoredNotesP = Webfield.getAll('/notes', {
    'content.authorids': user.profile.id,
    invitation: SUBMISSION_ID,
    noDetails: true
  });

  var edgesMapP = Webfield.getAll('/edges', {
    invitation: BID_ID,
    tail: user.profile.id
  })
  .then(function(edges) {
    return edges.reduce(function(noteMap, edge) {
      noteMap[edge.head] = edge;
      return noteMap;
    }, {});
  });

  return $.when(notesP, authoredNotesP, edgesMapP);
}


// Display the bid interface populated with loaded data
function renderContent(validNotes, authoredNotes, edgesMap) {
  var authoredNoteIds = _.map(authoredNotes, function(note){
    return note.id;
  });

  validNotes = _.filter(validNotes, function(note){
    return !_.includes(authoredNoteIds, note.original || note.id);
  })
  addEdgesToNotes(validNotes, edgesMap);

  var activeTab = 0;
  var sections;
  var binnedNotes;

  var paperDisplayOptions = {
    pdfLink: true,
    replyCount: true,
    showContents: true,
    showTags: false,
    showEdges: true,
    edgeInvitations: [invitation] // Bid invitation automatically available
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
    var updatedNote = _.find(validNotes, ['id', edgeObj.head]);
    if (!updatedNote) {
      return;
    }
    var prevEdgeIndex = _.findIndex(updatedNote.details.edges, ['invitation', BID_ID]);
    var prevVal = prevEdgeIndex !== -1 ?
      updatedNote.details.edges[prevEdgeIndex].label :
      'No Bid';

    if (edgeObj.ddate) {
      edgeObj.label = 'No Bid';
    }
    updatedNote.details.edges[prevEdgeIndex] = edgeObj;

    var labelToContainerId = {
      'Very High': 'veryHigh',
      'High': 'high',
      'Neutral': 'neutral',
      'Low': 'low',
      'Very Low': 'veryLow',
      'No Bid': 'noBid'
    };

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
      noBid: [],
      veryHigh: [],
      high: [],
      neutral: [],
      low: [],
      veryLow: []
    };

    var bids, n;
    for (var i = 0; i < notes.length; i++) {
      n = notes[i];
      bids = _.filter(n.details.edges, function(t) {
        return t.invitation === BID_ID;
      });

      if (bids.length) {
        if (bids[0].label === 'Very High') {
          binnedNotes.veryHigh.push(n);
        } else if (bids[0].label === 'High') {
          binnedNotes.high.push(n);
        } else if (bids[0].label === 'Neutral') {
          binnedNotes.neutral.push(n);
        } else if (bids[0].label === 'Low') {
          binnedNotes.low.push(n);
        } else if (bids[0].label === 'Very Low') {
          binnedNotes.veryLow.push(n);
        } else {
          binnedNotes.noBid.push(n);
        }
      } else {
        binnedNotes.noBid.push(n);
      }
    }

    var bidCount = binnedNotes.veryHigh.length + binnedNotes.high.length +
      binnedNotes.neutral.length + binnedNotes.low.length + binnedNotes.veryLow.length;

    $('#bidcount').remove();
    $('#header').append('<h4 id="bidcount">You have completed ' + bidCount + ' bids</h4>');

    var loadingContent = Handlebars.templates.spinner({ extraClasses: 'spinner-inline' });
    sections = [
      {
        heading: 'All Papers  <span class="glyphicon glyphicon-search"></span>',
        id: 'allPapers',
        content: null
      },
      {
        heading: 'No Bid',
        headingCount: binnedNotes.noBid.length,
        id: 'noBid',
        content: loadingContent
      },
      {
        heading: 'Very High',
        headingCount: binnedNotes.veryHigh.length,
        id: 'veryHigh',
        content: loadingContent
      },
      {
        heading: 'High',
        headingCount: binnedNotes.high.length,
        id: 'high',
        content: loadingContent
      },
      {
        heading: 'Neutral',
        headingCount: binnedNotes.neutral.length,
        id: 'neutral',
        content: loadingContent
      },
      {
        heading: 'Low',
        headingCount: binnedNotes.low.length,
        id: 'low',
        content: loadingContent
      },
      {
        heading: 'Very Low',
        headingCount: binnedNotes.veryLow.length,
        id: 'veryLow',
        content: loadingContent
      }
    ];
    sections[activeTab].active = true;

    $('#notes .tabs-container').remove();

    Webfield.ui.tabPanel(sections, {
      container: '#notes',
      hidden: true
    });

    // Render the contents of the All Papers tab
    var searchResultsOptions = _.assign({}, paperDisplayOptions, { container: '#allPapers' });
    var submissionListOptions = {
      heading: null,
      container: '#allPapers',
      search: {
        enabled: true,
        localSearch: false,
        subjectAreas: SUBJECT_AREAS,
        subjectAreaDropdown: 'basic',
        sort: false,
        onResults: function(searchResults) {
          Webfield.ui.searchResults(searchResults, searchResultsOptions);
        },
        onReset: function() {
          Webfield.ui.submissionList(notes, submissionListOptions);
        },
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: 2000,
      pageSize: 50,
      onPageClick: function(offset) {
        return Webfield.api.getSubmissions(BLIND_SUBMISSION_ID, {
          noDetails: true,
          pageSize: 50,
          offset: offset
        });
      },
      fadeIn: false
    };

    Webfield.ui.submissionList(notes, submissionListOptions);

    $('#notes > .spinner-container').remove();
    $('#notes .tabs-container').show();
  }

  function updateCounts() {
    var containers = [
      'noBid',
      'veryHigh',
      'high',
      'neutral',
      'low',
      'veryLow'
    ];
    var totalCount = 0;

    containers.forEach(function(containerId) {
      var $tab = $('ul.nav-tabs li a[href="#' + containerId + '"]');
      var numPapers = binnedNotes[containerId].length;

      $tab.find('span.badge').remove();
      if (numPapers) {
        $tab.append('<span class="badge">' + numPapers + '</span>');
      }

      if (containerId != 'noBid') {
        totalCount += numPapers;
      }
    });

    $('#bidcount').remove();
    $('#header').append('<h4 id="bidcount">You have completed ' + totalCount + ' bids</h4>');
  }

  updateNotes(validNotes);
}

function addEdgesToNotes(validNotes, edgesMap) {
  for (var i = 0; i < validNotes.length; i++) {
    var noteId = validNotes[i].id;
    if (edgesMap.hasOwnProperty(noteId)) {
      validNotes[i].details.edges = [edgesMap[noteId]];
    } else {
      validNotes[i].details.edges = [];
    }
  }
}

// Go!
main();