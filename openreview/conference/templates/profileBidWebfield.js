// webfield_template
// Remove line above if you don't want this page to be overwriten

// ------------------------------------
// Add Bid Interface
// ------------------------------------

var CONFERENCE_ID = '';
var HEADER = {};
var SHORT_PHRASE = '';
var PROFILE_GROUP_ID = '';
var BLIND_SUBMISSION_ID = '';
var BID_ID = '';
var SUBJECT_AREAS = '';
var CONFLICT_SCORE_ID = '';
var SCORE_IDS = [];

// Bid status data
var pageSize = 1000;
var selectedScore = SCORE_IDS.length && SCORE_IDS[0];
var activeTab = 0
var noteCount = 0;
var conflictIds = [];
var bidsByNote = {};
var bidsById = {
  'Very High': [],
  'High': [],
  'Neutral': [],
  'Very Low': [],
  'Low': []
};
var sections = [];

var paperDisplayOptions = {
  path: 'profile',
  openInNewTab: true,
  pdfLink: false,
  replyCount: false,
  showContents: true,
  showTags: false,
  showEdges: true,
  edgeInvitations: [invitation]
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

function getProfileNote(profile) {
  var position = _.upperFirst(_.get(profile.content.history, '[0].position', '')).trim()
  var institutionName = _.get(profile.content.history, '[0].institution.name', '').trim()
  var institutionDomain = _.get(profile.content.history, '[0].institution.domain', '').trim()
  var institution = institutionDomain
    ? institutionName + ' (' + institutionDomain + ')'
    : institutionName
  const separator = position && institution ? ' at ' : ''
  return {
    id: profile.id,
    forum: profile.id,
    content: {
      title: view.prettyId(profile.id) + ', ' + position + separator + institution,
      keywords: _.flatMap(profile.content.expertise, function(entry) { return entry.keywords; }).join(',')
    },
    tauthor: user.id
  }
}

function getPapersSortedByAffinity(offset) {
  if (selectedScore) {
    return Webfield.get('/edges', {
      invitation: selectedScore,
      tail: user.profile.id,
      sort: 'weight:desc',
      offset: offset,
      limit: pageSize
    })
    .then(function(result) {
      noteCount = result.count;

      if (noteCount > 0) {
        var edgesByHead = _.keyBy(result.edges, function(edge) {
          return edge.head;
        });
        var noteIds = Object.keys(edgesByHead);

        return Webfield.post('/profiles/search', {
          ids: noteIds
        })
        .then(function(result) {
          // Keep affinity score order
          var notesById = {};
          result.profiles.forEach(function(profile) {
            var profileNote = getProfileNote(profile);
            profile.content.names.forEach(function(name) {
              if (name.username) {
                notesById[name.username] = profileNote;
              }
            })
          });
          return noteIds
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
        return Webfield.get('/profiles', {
          group: PROFILE_GROUP_ID
        })
        .then(function(result) {
          noteCount = result.count;
          return result.profiles.map(function(profile) { return getProfileNote(profile); });
        })
      }
    });
  } else {
    return Webfield.get('/profiles', {
      group: PROFILE_GROUP_ID
    })
    .then(function(result) {
      noteCount = result.count;
      return result.profiles.map(function(profile) { return getProfileNote(profile); });
    })
  }
}

function getPapersByBids(bids, bidsByNote) {

  return Webfield.post('/profiles/search', {
    ids: bids.map(function(bid) { return bid.head; })
  })
  .then(function(result) {
    return addEdgesToNotes(result.profiles.map(function(profile) { return getProfileNote(profile); }), bidsByNote);
  });
}

// Perform all the required API calls
function load() {

  var sortedNotesP = getPapersSortedByAffinity(0, selectedScore);

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
      getPapersByBids(bidsById[bidId], bidsByNote).then(function(notes) {
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
    var previousEdge = bidsByNote[edge.head];

    if (edge.ddate) {
      delete bidsByNote[edge.head];
      bidsById[edge.label] = bidsById[edge.label].filter(function(e) { return edge.id !== e.id; });
    } else {
      bidsByNote[edge.head] = edge;
      bidsById[edge.label].push(edge);
      if (previousEdge) {
        bidsById[previousEdge.label] = bidsById[previousEdge.label].filter(function(e) { return previousEdge.id !== e.id; });
      }
    }

    // If not on the All Papers tab, fade out note when bid is changed
    if (activeTab !== 0) {
      $(e.currentTarget).find('.btn-group').addClass('disabled');

      setTimeout(function() {
        var $elem = $(e.currentTarget).closest('.note');
        $elem.fadeOut('fast', function() {
          var $parent = $elem.parent();
          $elem.remove();

          if (!$parent.children().length) {
            $parent.append('<li><p class="empty-message">No papers to display at this time</p></li>');
          }
        });
      }, 100);

      // Change bid in the All Papers tab
      var $noteToChange = $('#all-papers .submissions-list .note[data-id="' + previousEdge.head + '"] .btn-group');
      if (edge.ddate) {
        $noteToChange.button('toggle').children('input').prop('checked', false);
      } else {
        $noteToChange.find('label[data-value="' + edge.label + '"]').button('toggle');
      }
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
    return getPapersSortedByAffinity(0, selectedScore)
    .then(function(notes) {
      return updateNotes(prepareNotes(notes, conflictIds, bidsByNote));
    });
  });

  updateNotes(validNotes);
}

function prepareNotes(notes, conflictIds, edgesMap) {
  var validNotes = _.filter(notes, function(note) {
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

function updateNotes(notes) {
  var bidCount = 0;
  $('#bidcount').remove();
  $('#header').append('<h4 id="bidcount">You have completed ' + bidCount + ' bids</h4>');

  var loadingContent = Handlebars.templates.spinner({ extraClasses: 'spinner-inline' });
  sections = [
    {
      heading: 'All Area Chairs  <span class="glyphicon glyphicon-search"></span>',
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
  var searchResultsOptions = _.assign({}, paperDisplayOptions, { container: '#allPapers', emptyMessage: 'No Area Chairs to display at this time' });
  var submissionListOptions = {
    heading: null,
    container: '#allPapers',
    search: {
      enabled: true,
      localSearch: true,
      subjectAreas: SUBJECT_AREAS,
      subjectAreaDropdown: 'basic',
      invitation: BLIND_SUBMISSION_ID,
      placeholder: 'Search by name and metadata',
      sort: false,
      onResults: function(searchResults) {
        Webfield.ui.searchResults(prepareNotes(searchResults, conflictIds, bidsByNote), searchResultsOptions);
      },
      onReset: function() {
        Webfield.ui.searchResults(notes, searchResultsOptions);
        $('#allPapers').append(view.paginationLinks(noteCount, pageSize, 1));
      },
    },
    displayOptions: paperDisplayOptions,
    autoLoad: false,
    noteCount: noteCount,
    pageSize: pageSize,
    onPageClick: function(offset) {
      return getPapersSortedByAffinity(offset, selectedScore)
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
