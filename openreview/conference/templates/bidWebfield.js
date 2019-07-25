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

function getPapersSortedByAffinity(offset) {
  return Webfield.get('/edges', {
    invitation: CONFERENCE_ID + '/-/Reviewing/Affinity_Score',
    tail: user.profile.id,
    offset: offset,
    limit: 50
  })
  .then(function(result) {
    var noteIds = result.edges.map(function(edge) {
      return edge.head;
    });

    return Webfield.post('/notes/search', {
      ids: noteIds
    })
    .then(function(result) {
      return result.notes;
    })
  });
}

function getPapersByBids(bids, bidsByNote) {

  return Webfield.post('/notes/search', {
    ids: bids.map(function(bid) { return bid.head; })
  })
  .then(function(result) {
    return addEdgesToNotes(result.notes, bidsByNote);
  });
}

function getBidCounts(edgesMap) {
  var containers = {
    'No Bid': 0,
    'Very High': 0,
    'High': 0,
    'Neutral': 0,
    'Low': 0,
    'Very Low': 0
  };
  var totalCount = 0;

  for (key in edgesMap) {
    var label = edgesMap[key].label;
    containers[label] += 1;
  }

  return containers;
}




// Perform all the required API calls
function load() {

  var sortedNotesP = getPapersSortedByAffinity(0);

  var conflictIdsP = Webfield.getAll('/edges', {
    invitation: CONFERENCE_ID + '/-/Reviewing/Conflict',
    tail: user.profile.id
  })
  .then(function(edges) {
    return edges.map(function(edge) {
      return edge.head;
    });
 });

  var bidEdgesP = Webfield.getAll('/edges', {
    invitation: BID_ID,
    tail: user.profile.id
  });

  return $.when(sortedNotesP, conflictIdsP, bidEdgesP);
}


// Display the bid interface populated with loaded data
function renderContent(notes, conflictIds, bidEdges) {

  var activeTab = 0;
  var sections;
  var bidsByNote = {};
  var bidsById = {
    'Very High': [],
    'High': [],
    'Neutral': [],
    'Very Low': [],
    'Low': []
  };

  bidEdges.forEach(function(edge) {
    bidsByNote[edge.head] = edge;
    bidsById[edge.label].push(edge);
  });

  var validNotes = prepareNotes(notes, conflictIds, bidsByNote);

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
    var bidId = sections[activeTab].heading;

    if (containerId !== 'allPapers') {

      getPapersByBids(bidsById[bidId], bidsByNote)
      .then(function(notes) {
        Webfield.ui.submissionList(notes, {
          heading: null,
          container: '#' + containerId,
          search: { enabled: false },
          displayOptions: paperDisplayOptions,
          fadeIn: false
        });
      })
    }
  });

  $('#invitation-container').on('hidden.bs.tab', 'ul.nav-tabs li a', function(e) {
    var containerId = $(e.target).attr('href');
    if (containerId !== '#allPapers') {
      Webfield.ui.spinner(containerId, {inline: true});
    }
  });

  $('#invitation-container').on('bidUpdated', '.tag-widget', function(e, edge) {
    if (edge.ddate) {
      delete bidsByNote[edge.head];
      bidsById[edge.label] = bidsById[edge.label].filter(function(e) { return edge.id != e.id; });
    } else {
      bidsByNote[edge.head] = edge;
      bidsById[edge.label].push(edge);
    }

    // var updatedNote = _.find(validNotes, ['id', edgeObj.head]);
    // if (!updatedNote) {
    //   return;
    // }
    // var prevEdgeIndex = _.findIndex(updatedNote.details.edges, ['invitation', BID_ID]);
    // var prevVal = prevEdgeIndex !== -1 ?
    //   updatedNote.details.edges[prevEdgeIndex].label :
    //   'No Bid';

    // if (edgeObj.ddate) {
    //   edgeObj.label = 'No Bid';
    // }
    // updatedNote.details.edges[prevEdgeIndex] = edgeObj;

    // var labelToContainerId = {
    //   'Very High': 'veryHigh',
    //   'High': 'high',
    //   'Neutral': 'neutral',
    //   'Low': 'low',
    //   'Very Low': 'veryLow',
    //   'No Bid': 'noBid'
    // };

    // var previousNoteList = binnedNotes[labelToContainerId[prevVal]];
    // var currentNoteList = binnedNotes[labelToContainerId[edgeObj.label]];

    // var currentIndex = _.findIndex(previousNoteList, ['id', edgeObj.head]);
    // if (currentIndex !== -1) {
    //   var currentNote = previousNoteList[currentIndex];
    //   currentNote.details.edges = [edgeObj]; // Assumes notes will have only 1 type of edge
    //   previousNoteList.splice(currentIndex, 1);
    //   currentNoteList.push(currentNote);
    // } else {
    //   console.warn('Note not found!');
    // }

    // If the current tab is not the All Papers tab remove the note from the DOM and
    // update the state of edge widget in the All Papers tab
    // if (activeTab) {
    //   var $elem = $(e.target).closest('.note');
    //   $elem.fadeOut('normal', function() {
    //     $elem.remove();

    //     var $container = $('#' + labelToContainerId[prevVal] + ' .submissions-list');
    //     if (!$container.children().length) {
    //       $container.append('<li><p class="empty-message">No papers to display at this time</p></li>');
    //     }
    //   });

    //   var $noteToChange = $('#allPapers .submissions-list .note[data-id="' + updatedNote.id + '"]');
    //   $noteToChange.find('label[data-value="' + prevVal + '"]').removeClass('active')
    //     .children('input').prop('checked', false);
    //   $noteToChange.find('label[data-value="' + edgeObj.label + '"]').button('toggle');
    // }

     updateCounts();
  });

  function updateNotes(notes) {

    var bidCount = 0;
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
        headingCount: 0,
        id: 'noBid',
        content: loadingContent
      },
      {
        heading: 'Very High',
        headingCount: bidsById['Very High'].length,
        id: 'veryHigh',
        content: loadingContent
      },
      {
        heading: 'High',
        headingCount: bidsById['High'].length,
        id: 'high',
        content: loadingContent
      },
      {
        heading: 'Neutral',
        headingCount: bidsById['Neutral'].length,
        id: 'neutral',
        content: loadingContent
      },
      {
        heading: 'Low',
        headingCount: bidsById['Low'].length,
        id: 'low',
        content: loadingContent
      },
      {
        heading: 'Very Low',
        headingCount: bidsById['Very Low'].length,
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
          Webfield.ui.searchResults(prepareNotes(searchResults, conflictIds, bidsByNote), searchResultsOptions);
        },
        onReset: function() {
          Webfield.ui.submissionList(notes, submissionListOptions);
        },
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: 1600,
      pageSize: 50,
      onPageClick: function(offset) {
        return getPapersSortedByAffinity(offset)
        .then(function(notes) {
          return prepareNotes(notes, conflictIds, bidsByNote);
        });
      },
      fadeIn: false
    };

    Webfield.ui.submissionList(notes, submissionListOptions);

    $('#notes > .spinner-container').remove();
    $('#notes .tabs-container').show();
  }

  function updateCounts() {

    var totalCount = 0;

    for(var i = 2; i < sections.length; i++) {
      var $tab = $('ul.nav-tabs li a[href="#' + sections[i].id + '"]');
      var numPapers = bidsById[sections[i].heading].length;

      $tab.find('span.badge').remove();
      if (numPapers) {
        $tab.append('<span class="badge">' + numPapers + '</span>');
      }

      if (sections[i].heading != 'noBid') {
        totalCount += numPapers;
      }
    };

    $('#bidcount').remove();
    $('#header').append('<h4 id="bidcount">You have completed ' + totalCount + ' bids</h4>');
  }

  updateNotes(validNotes);
}

function prepareNotes(notes, conflictIds, edgesMap) {
  var validNotes = _.filter(notes, function(note){
    return !_.includes(conflictIds, note.original || note.id);
  })
  return addEdgesToNotes(validNotes, edgesMap);
}

function addEdgesToNotes(validNotes, edgesMap) {
  for (var i = 0; i < validNotes.length; i++) {
    var noteId = validNotes[i].id;
    if (edgesMap.hasOwnProperty(noteId)) {
      validNotes[i].details = {
        edges: [edgesMap[noteId]]
      };
    } else {
      validNotes[i].details = {
        edges: []
      };
    }
  }
  return validNotes;
}

// Go!
main();