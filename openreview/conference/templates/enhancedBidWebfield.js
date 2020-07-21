// ------------------------------------
// Add Bid Interface
// ------------------------------------

var CONFERENCE_ID = 'ICLR.cc/2020/Conference';
var HEADER = {"title": "ICLR 2020 Bidding Console", "instructions": "\n            <p class=\"dark\"><strong>Instructions:</strong></p>\n            <ul>\n                <li>\n                    Please indicate your <strong>level of interest</strong> in\n                    reviewing the submitted papers below,\n                    on a scale from \"Very Low\" interest to \"Very High\" interest.\n                </li>\n                <li>\n                    Please bid on as many papers as possible\n                    to ensure that your preferences are taken into account.\n                </li>\n                <li>\n                    Use the search field to filter papers by keyword or subject area.\n                </li>\n            </ul>\n            <p class=\"dark\"><strong>A few tips:</strong></p>\n            <ul>\n                <li>\n                    Papers for which you have a conflict of interest are not shown.\n                </li>\n                <li>\n                    Positive bids (\"High\" and \"Very High\") will, in most cases, increase the likelihood that you will be assigned that paper.\n                </li>\n                <li>\n                    Negative bids (\"Low\" and \"Very Low\") will, in most cases, decrease the likelihood that you will be assigned that paper.\n                </li>\n                \n            <li>\n                Papers are sorted based on keyword similarity with the papers\n                that you provided in the Expertise Selection Interface.\n            </li>\n            </ul>\n            <br>"};
var SHORT_PHRASE = '';
var BLIND_SUBMISSION_ID = 'ICLR.cc/2020/Conference/-/Blind_Submission';
var BID_ID = 'ICLR.cc/2020/Conference/Reviewers/-/Bid';
var SUBJECT_AREAS = [];
var AFFINITY_SCORE_ID = 'ICLR.cc/2020/Conference/Reviewers/-/Affinity_Score';
var CONFLICT_SCORE_ID = 'ICLR.cc/2020/Conference/Reviewers/-/Conflict';
var BID_VALUES = [0, 1, 2, 3, 4];
var TRADE_OFF = 1;
var noteCount = 0;

// Main is the entry point to the webfield code and runs everything
function main() {
  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.header(HEADER.title, HEADER.instructions);

  Webfield.ui.spinner('#notes', { inline: true });

  load().then(renderContent).then(Webfield.ui.done);
}

function getBidsCount() {
  return Webfield.get('/edges', {
    invitation: BID_ID,
    groupBy: 'head',
    select: 'count'
  })
  .then(function(result) {
    return _.reduce(result.groupedEdges, function(idToBids, edge) {
      idToBids[edge.id.head] = edge.count;
      return idToBids;
    }, {});
  });
}

function getAffinityScores() {
  return Webfield.get('/edges', {
    invitation: AFFINITY_SCORE_ID,
    tail: user.profile.id,
    groupBy: 'head',
    select: 'weight'
  })
  .then(function(result) {
    return _.reduce(result.groupedEdges, function(idToScore, edge) {
      idToScore[edge.id.head] = edge.values[0].weight;
      return idToScore;
    }, {});
  });
}

function paperScoringFunction(value) {
  return Math.sqrt(value);
}

function getPaperScores(affinityScores, bidsCount) {
  var paperScores = [];
  var noteIds = Object.keys(affinityScores);
  for (var i = 0; i < noteIds.length; i++) {
    var partialScore = 0;
    var noteId = noteIds[i];
    var affinityScore = affinityScores[noteId];
    var numberOfBids = bidsCount[noteId];
    for (var j = 0; j < BID_VALUES.length; j++) {
      var bidValue = BID_VALUES[j];
      partialScore = partialScore + paperScoringFunction(numberOfBids + bidValue) - paperScoringFunction(numberOfBids);
    }
    paperScores.push({
      id: noteId,
      score: -1 * (partialScore * affinityScore / BID_VALUES.length + TRADE_OFF * (Math.pow(2, affinityScore) - 1))
    });
  }
  return _.sortBy(paperScores, [ 'score' ]);
}

function getPapersSortedByAlgo(paperScores, offset) {
  var limit = 50;
  if (!paperScores.length) {
    return Webfield.get('/notes', {
      invitation: BLIND_SUBMISSION_ID,
      offset: offset,
      limit: limit
    })
    .then(function(result) {
      noteCount = result.count;
      return result.notes;
    });
  }
  noteCount = paperScores.length;
  var notes = paperScores.slice(offset, offset + limit);
  var noteIds = _.map(notes, function(note) {
    return note.id;
  });
  return Webfield.post('/notes/search', {
    ids: noteIds
  })
  .then(function(result) {
    //Keep score order
    var notesById = _.keyBy(result.notes, function(note) {
      return note.id;
    });
    return noteIds.map(function(id) {
      return notesById[id];
    });
  });
}

function getPapersSortedByAffinity(offset) {
  if (AFFINITY_SCORE_ID) {
    return Webfield.get('/edges', {
      invitation: AFFINITY_SCORE_ID,
      tail: user.profile.id,
      sort: 'weight:desc',
      offset: offset,
      limit: 50
    })
    .then(function(result) {
      noteCount = result.count;

      if (noteCount > 0) {
        var edgesByHead = _.keyBy(result.edges, function(edge) {
          return edge.head;
        });
        var noteIds = Object.keys(edgesByHead);

        return Webfield.post('/notes/search', {
          ids: noteIds
        })
        .then(function(result) {
          //Keep affinity score order
          var notesById = _.keyBy(result.notes, function(note) {
            return note.id;
          });
          return noteIds.filter(function(id) {
            if (notesById[id] && notesById[id].invitation === BLIND_SUBMISSION_ID) {
              return notesById[id];
            }
          })
          .map(function(id) {
            var note = notesById[id];
            var edge = edgesByHead[id];
            //to render the edge widget correctly
            edge.signatures = [];
            note.details = {
              edges: [edge]
            }
            return note;
          });
        });
      } else {
        return Webfield.get('/notes', {
          invitation: BLIND_SUBMISSION_ID,
          offset: offset,
          limit: 50
        })
        .then(function(result) {
          noteCount = result.count;
          return result.notes;
        });
      }
    });
  } else {
    return Webfield.get('/notes', {
      invitation: BLIND_SUBMISSION_ID,
      offset: offset,
      limit: 50
    })
    .then(function(result) {
      noteCount = result.count;
      return result.notes;
    })
  }

}

function getPapersByBids(bids, bidsByNote) {

  return Webfield.post('/notes/search', {
    ids: bids.map(function(bid) { return bid.head; })
  })
  .then(function(result) {
    return addEdgesToNotes(result.notes, bidsByNote);
  });
}

// Perform all the required API calls
function load() {
  var affinityScoresP = getAffinityScores();
  var bidsCountP = getBidsCount();
  return $.when(affinityScoresP, bidsCountP)
    .then(function(affinityScores, bidsCount) {
      var paperScores = getPaperScores(affinityScores, bidsCount);
      var sortedNotesP = getPapersSortedByAlgo(paperScores, 0);

      var conflictIdsP = Webfield.getAll('/edges', {
        invitation: CONFLICT_SCORE_ID,
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
      return {
        paperScores: paperScores,
        sortedNotesP: sortedNotesP,
        conflictIdsP: conflictIdsP,
        bidEdgesP: bidEdgesP
      }
    })
    .then(function(data) {
      return $.when(data.paperScores, data.sortedNotesP, data.conflictIdsP, data.bidEdgesP);
    })
}
// function load() {

//   var sortedNotesP = getPapersSortedByAffinity(0);

//   var conflictIdsP = Webfield.getAll('/edges', {
//     invitation: CONFLICT_SCORE_ID,
//     tail: user.profile.id
//   })
//   .then(function(edges) {
//     return edges.map(function(edge) {
//       return edge.head;
//     });
//  });

//   var bidEdgesP = Webfield.getAll('/edges', {
//     invitation: BID_ID,
//     tail: user.profile.id
//   });

//   return $.when(sortedNotesP, conflictIdsP, bidEdgesP);
// }


// Display the bid interface populated with loaded data
function renderContent(paperScores, notes, conflictIds, bidEdges) {

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
      });
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
      bidsById[edge.label] = bidsById[edge.label].filter(function(e) { return edge.id !== e.id; });
    } else {
      var previousEdge = bidsByNote[edge.head];
      bidsByNote[edge.head] = edge;
      bidsById[edge.label].push(edge);
      if (previousEdge) {
        bidsById[previousEdge.label] = bidsById[previousEdge.label].filter(function(e) { return previousEdge.id !== e.id; });
      }
    }

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
        invitation: BLIND_SUBMISSION_ID,
        sort: false,
        onResults: function(searchResults) {
          Webfield.ui.searchResults(prepareNotes(searchResults, conflictIds, bidsByNote), searchResultsOptions);
        },
        onReset: function() {
          Webfield.ui.searchResults(notes, searchResultsOptions);
          $('#allPapers').append(view.paginationLinks(noteCount, 50, 1));
        },
      },
      displayOptions: paperDisplayOptions,
      autoLoad: false,
      noteCount: noteCount,
      pageSize: 50,
      onPageClick: function(offset) {
        return getPapersSortedByAlgo(paperScores, offset)
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

    for(var i = 1; i < sections.length; i++) {
      var $tab = $('ul.nav-tabs li a[href="#' + sections[i].id + '"]');
      var numPapers = bidsById[sections[i].heading].length;

      $tab.find('span.badge').remove();
      if (numPapers) {
        $tab.append('<span class="badge">' + numPapers + '</span>');
      }

      totalCount += numPapers;
    };

    $('#bidcount').remove();
    $('#header').append('<h4 id="bidcount">You have completed ' + totalCount + ' bids</h4>');
  }

  updateNotes(validNotes);
  updateCounts();
}

function prepareNotes(notes, conflictIds, edgesMap) {
  var validNotes = _.filter(notes, function(note){
    return !_.includes(conflictIds, note.id);
  })
  return addEdgesToNotes(validNotes, edgesMap);
}

function addEdgesToNotes(validNotes, edgesMap) {
  for (var i = 0; i < validNotes.length; i++) {
    var note = validNotes[i];
    if (!_.has(note, 'details.edges')) {
      note.details = {
        edges: []
      }
    }
    if (edgesMap.hasOwnProperty(note.id)) {
      note.details.edges.push(edgesMap[note.id]);
    };
  }
  return validNotes;
}

// Go!
main();
