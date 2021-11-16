// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Add Bid Interface
// ------------------------------------

var CONFERENCE_ID = '';
var HEADER = {};
var SHORT_PHRASE = '';
var BLIND_SUBMISSION_ID = '';
var BID_ID = '';
var SUBJECT_AREAS = '';
var CONFLICT_SCORE_ID = '';
var SCORE_IDS = [];
var SCORE_IDS_WITH_SUPER = [];
var ENABLE_SUPER_ALGO = false;
var BID_OPTIONS = [];
// In the SUPER* algorithm, we will map only positive bids to a bid, and treat
// not positive bids as no bids in the algorithm. The following variables enforce this.
var POSITIVE_BIDS = [];
var BID_VALUES = [ 1 ];
// The following parameter will dictate how much the algorithm optimizes for
// showing relevant papers to reviewers versus optimizing for each paper getting
// a sufficient number of bids. Specifically as the TRADE_OFF parameter goes up, 
// the ordering will get closer to showing the papers in decreasing order of 
// the relevance scores, and as the TRADE_OFF parameter goes down, the ordering
// will get closer to showing the papers in increasing order of the number of bids.
// The value of 1 is a relatively higher choice.
var TRADE_OFF = 1;

// Bid status data
var selectedScore = SCORE_IDS.length && SCORE_IDS[0];
var activeTab = 0;
var noteCount = 0;
var conflictIds = [];
var bidsByNote = {};
var bidsById = BID_OPTIONS.reduce(function(bidDict, option) {
  bidDict[option] = [];
  return bidDict;
}, {});
var sections = [];

var paperDisplayOptions = {
  pdfLink: true,
  replyCount: true,
  showContents: true,
  showTags: false,
  showEdges: true,
  edgeInvitations: [invitation], // Bid invitation automatically available
  referrer: encodeURIComponent('[Bidding Console](/invitation?id=' + invitation.id + ')')
};

// Main is the entry point to the webfield code and runs everything
function main() {
  if (args && args.referrer) {
    OpenBanner.referrerLink(args.referrer);
  } else {
    OpenBanner.venueHomepageLink(CONFERENCE_ID);
  }

  Webfield.ui.setup('#invitation-container', CONFERENCE_ID);  // required

  Webfield.ui.header(HEADER.title, HEADER.instructions);

  Webfield.ui.spinner('#notes', { inline: true });

  load().then(renderContent).then(Webfield.ui.done);
}

function getBidsCount() {
  return Webfield.get('/edges', {
    invitation: BID_ID,
    groupBy: 'label,head',
    select: 'count'
  })
  .then(function(result) {
    return _.reduce(result.groupedEdges, function(idToBids, edge) {
      if (idToBids[edge.id.head] === undefined) {
        idToBids[edge.id.head] = {};
      } 
      idToBids[edge.id.head][edge.id.label] = edge.count;
      return idToBids;
    }, {});
  });
}


function getAffinityScores() {
  var invitation = selectedScore;
  if (_.startsWith(selectedScore, 'SUPER_')) {
    invitation = selectedScore.substring(6);
  }
  return Webfield.get('/edges', {
    invitation: invitation,
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
    if (bidsCount[noteId] === undefined) {
      var numberOfBids = 0;
    } else {
      var numberOfBids = 0;
      for (var key in bidsCount[noteId]) {
        if (_.includes(POSITIVE_BIDS, key)) {
          var value = bidsCount[noteId][key];
          numberOfBids = numberOfBids + value;
        }
      }
    }
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
  if (selectedScore) {
    return Webfield.get('/edges', {
      invitation: selectedScore,
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
          // Keep affinity score order
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
            };
            return note;
          });
        });
      } else {
        return Webfield.get('/notes', {
          invitation: BLIND_SUBMISSION_ID,
          details: 'invitation',
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
      details: 'invitation',
      offset: offset,
      limit: 50
    })
    .then(function(result) {
      noteCount = result.count;
      return result.notes;
    });
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
  var sortedNotesP
  if (_.startsWith(selectedScore, 'SUPER_')) {
    sortedNotesP = $.when(getAffinityScores(), getBidsCount())
      .then(function(affinityScores, bidsCount) {
        return getPapersSortedByAlgo(getPaperScores(affinityScores, bidsCount), 0);
      });
  } else {
    sortedNotesP = getPapersSortedByAffinity(0);
  }
  
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

  return $.when(sortedNotesP, conflictIdsP, bidEdgesP);
}


// Display the bid interface populated with loaded data
function renderContent(notes, conflicts, bidEdges) {

  conflictIds = conflicts;

  bidEdges.forEach(function(edge) {
    bidsByNote[edge.head] = edge;
    bidsById[edge.label].push(edge);
  });

  var validNotes = prepareNotes(notes, conflictIds, bidsByNote);

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

    // If not on the All Papers tab, fade out note when bid is changed
    if (activeTab !== 0) {
      setTimeout(function() {
        $(e.currentTarget).closest('.note').fadeOut();
      }, 500);
    }

    updateCounts();
  });

  $('#invitation-container').on('apiReturnedError', '.tag-widget', function (e, error) {
    if (error.path === 'too many edges') {
      setTimeout(function () { location.reload(); }, 1000);
    }
  });

  $('#invitation-container').on('change', 'form.notes-search-form .score-dropdown', function(e) {
    selectedScore = $(this).val();

    var sortedNotesP;
    if (_.startsWith(selectedScore, 'SUPER_')) {
      sortedNotesP = $.when(getAffinityScores(), getBidsCount())
        .then(function(affinityScores, bidsCount) {
          return getPapersSortedByAlgo(getPaperScores(affinityScores, bidsCount), 0);
        });
    } else {
      sortedNotesP = getPapersSortedByAffinity(0);
    }

    return sortedNotesP
    .then(function(notes) {
      return updateNotes(prepareNotes(notes, conflictIds, bidsByNote));
    });
  });

  updateNotes(validNotes);
}

function prepareNotes(notes, conflictIds, edgesMap) {
  var validNotes = _.filter(notes, function(note) {
    return !_.includes(conflictIds, note.id);
  });
  return addEdgesToNotes(validNotes, edgesMap);
}

function addEdgesToNotes(validNotes, edgesMap) {
  for (var i = 0; i < validNotes.length; i++) {
    var note = validNotes[i];
    if (!_.has(note, 'details.edges')) {
      note.details = {
        edges: []
      };
    }
    if (edgesMap.hasOwnProperty(note.id)) {
      note.details.edges.push(edgesMap[note.id]);
    };
  }
  return validNotes;
}

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
    }
  ];

  BID_OPTIONS.forEach(function(option) {
    sections.push({
      heading: option,
      headingCount: bidsById[option].length,
      id: option.replace(' ', '').toLowerCase(),
      content: loadingContent
    })
  });

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
      var sortedNotesP;
      if (_.startsWith(selectedScore, 'SUPER_')) {
        sortedNotesP = $.when(getAffinityScores(), getBidsCount())
          .then(function(affinityScores, bidsCount) {
            return getPapersSortedByAlgo(getPaperScores(affinityScores, bidsCount), offset);
          });
      } else {
        sortedNotesP = getPapersSortedByAffinity(offset);
      }
      return sortedNotesP
      .then(function(notes) {
        return prepareNotes(notes, conflictIds, bidsByNote);
      });
    },
    fadeIn: false
  };

  Webfield.ui.submissionList(notes, submissionListOptions);


  if (SCORE_IDS.length) {

    var optionsHtml = '';
    SCORE_IDS.forEach(function(scoreId) {
      var label = view.prettyInvitationId(scoreId);
      var selectedClass = selectedScore == scoreId && 'selected';
      optionsHtml = optionsHtml + '<option value="' + scoreId + '" ' + selectedClass + '>' + label + '</option>';
    })

    if (ENABLE_SUPER_ALGO) {
      SCORE_IDS.forEach(function(scoreId) {
        // Only add SUPER to the specified scores
        if (_.includes(SCORE_IDS_WITH_SUPER, scoreId)) return;
        var label = 'SUPER ' + view.prettyInvitationId(scoreId);
        var superScoreId = 'SUPER_' + scoreId;
        var selectedClass = selectedScore == superScoreId && 'selected';
        optionsHtml = optionsHtml + '<option value="' + superScoreId + '" ' + selectedClass + '>' + label + '</option>';
      })
    }

    $('#notes .form-inline.notes-search-form').append(
      '<div class="form-group score">' +
      '<label for="score-dropdown">Sort By:</label>' +
      '<select class="score-dropdown form-control">' +
      optionsHtml +
      '</select>' +
      '</div>'
    );
  }

  $('#notes > .spinner-container').remove();
  $('#notes .tabs-container').show();

  updateCounts();
}

function updateCounts() {
  var totalCount = 0;

  for (var i = 1; i < sections.length; i++) {
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

// Go!
main();
