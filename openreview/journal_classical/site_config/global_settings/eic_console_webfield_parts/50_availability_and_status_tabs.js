var getAvailabilityLabel = function(state) {
  return state === 'available' ? 'Available' : 'Unavailable';
};

var getAvailabilityWeight = function(state, monthValue) {
  return state === 'until' ? Number(monthValue) : null;
};

var getMonthOptions = function(count) {
  var now = new Date();
  var options = [];
  for (var i = 1; i <= count; i += 1) {
    var month = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + i, 1));
    options.push({
      value: month.getTime(),
      label: month.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
    });
  }
  return options;
};

var getAvailabilityState = function(data) {
  var label = data && data.label || 'Available';
  var weight = Number(data && data.weight);
  if (label === 'Unavailable' && (!weight || weight > Date.now())) {
    return weight ? 'until' : 'indefinite';
  }
  return 'available';
};

var getAvailabilityMonthValue = function(data, monthOptions) {
  var weight = Number(data && data.weight);
  if (weight && weight > Date.now()) {
    return weight;
  }
  return monthOptions[0].value;
};

var postAvailabilityEdge = function(data, state, monthValue) {
  if (!data) {
    return $.Deferred().resolve().promise();
  }
  var label = getAvailabilityLabel(state);
  var weight = getAvailabilityWeight(state, monthValue);
  var currentWeight = data.weight === undefined || data.weight === null ? null : Number(data.weight);
  var edge = {
    invitation: data.invitationId,
    signatures: [EDITORS_IN_CHIEF_ID],
    head: data.headId,
    tail: data.tailId,
    label: label,
    weight: weight
  };
  if (data.edgeId) {
    edge.id = data.edgeId;
  }
  if (data.label === label && currentWeight === weight) {
    return $.Deferred().resolve().promise();
  }
  return Webfield2.api.post('/edges', edge);
};

var renderRoleStatisticsTab = function(conferenceStats) {
  var referrerUrl = encodeURIComponent('[Editors-in-Chief Console](/group?id=' + EDITORS_IN_CHIEF_ID + '#paper-status)');

  var renderStatContainer = function(title, stat, hint, extraClasses) {
    return '<div class="col-md-4 col-xs-6 mb-3 ' + (extraClasses || '') + '">' +
      '<h4>' + title + '</h4>' +
      stat +
      (hint ? '<p class="hint">' + hint + '</p>' : '') +
      '</div>';
  };

  var getDueDateStatus = function(date) {
    var day = 24 * 60 * 60 * 1000;
    var diff = Date.now() - date.getTime();

    if (diff > 0) {
      return 'expired';
    }
    if (diff > -3 * day) {
      return 'warning';
    }
    return '';
  };

  var renderCombinedTasksList = function(invPairs) {
    var resultHtml = '';
    if (invPairs.length > 0) {
      resultHtml += '<ul class="list-unstyled submissions-list task-list eic-task-list mt-0 mb-0">'
      invPairs.forEach(function(forumInv) {
        var dateFormatOptions = {
          hour: 'numeric', minute: 'numeric', day: '2-digit', month: 'short', year: 'numeric', timeZoneName: 'long'
        };
        var inv = forumInv[1]

        if (inv.cdate > Date.now()) {
          var startDate = new Date(inv.cdate);
          inv.startDateStr = startDate.toLocaleDateString('en-GB', dateFormatOptions);
        }
        var duedate = new Date(inv.duedate);
        inv.dueDateStr = duedate.toLocaleDateString('en-GB', dateFormatOptions);
        inv.dueDateStatus = getDueDateStatus(duedate);
        resultHtml += (
          '<li class="note">' +
            '<p class="mb-1"><strong><a href="/forum?id=' + forumInv[0].id + '&invitationId=' + inv.id + '&referrer=' + referrerUrl + '" target="_blank">' +
            forumInv[0].title + ': ' + view.prettyInvitationId(inv.id) +
            '</a></strong></p>' +
            (inv.startDateStr ? '<p class="mb-1"><span class="duedate" style="margin-left: 0;">Start: ' + inv.startDateStr + '</span></p>' : '') +
            '<p class="mb-1"><span class="duedate ' + inv.dueDateStatus +'" style="margin-left: 0;">Due: ' + inv.dueDateStr + '</span></p>' +
          '</li>'
        );
      });
      resultHtml += '</ul>';
    } else {
      resultHtml += '<p class="empty-message mb-3">No tasks to complete.</p>';
    }
    return resultHtml;
  }

  // Conference statistics
  var html = '<div class="container"><div class="row text-center" style="margin-top: .5rem;">';
  html += renderStatContainer(
    'Reviewers:',
    '<h3>' + conferenceStats.numReviewers + '</h3>',
    '<a href="/group/edit?id=' + REVIEWERS_ID + '">Reviewers Group</a>',
    'col-md-offset-2'
  );
  html += renderStatContainer(
    'Top Reviewers:',
    '<h3>' + conferenceStats.numExpertReviewers + '</h3>',
    '<a href="/group/edit?id=' + EXPERT_REVIEWERS_ID + '">Top Reviewers Group</a>'
  );
  html += renderStatContainer(
    'Action Editors:',
    '<h3>' + conferenceStats.numActionEditors + '</h3>',
    '<a href="/group/edit?id=' + ACTION_EDITOR_ID + '">Action Editors Group</a>'
  );
  html += '</div>';
  html += '<hr class="spacer" style="margin-bottom: 1rem; margin-top: .5rem;">';

  html += '<div class="row text-center" style="margin-top: .5rem;">';
  html += renderStatContainer(
    'Submitted Papers:',
    '<h3>' + conferenceStats.numSubmitted + '</h3>'
  );
  html += renderStatContainer(
    'Papers Under Review:',
    '<h3>' + conferenceStats.numUnderReview + '</h3>'
  );
  html += renderStatContainer(
    'Decision Made:',
    '<h3>' + conferenceStats.numDecisionMade + '</h3>'
  );
  html += renderStatContainer(
    'Accepted Papers:',
    '<h3>' + conferenceStats.numAccepted + '</h3>'
  );
  html += renderStatContainer(
    'Rejected Papers:',
    '<h3>' + conferenceStats.numRejected + '</h3>'
  );
  html += renderStatContainer(
    'Retracted Papers:',
    '<h3>' + conferenceStats.numRetracted + '</h3>'
  );
  html += '</div>';
  html += '<hr class="spacer" style="margin-bottom: 1rem; margin-top: 0;">';

  html += '<div class="row" style="margin-top: .5rem;">';
  html += '<div class="col-md-4 col-xs-6">';
  html += '<h4>Important Invitations:</h4>';
  html += '<p class="mb-1"><strong>Venue:</strong></p>';
  html += '<ul style="padding-left: 15px">';
  html += conferenceStats.superInvitationIds.map(function(inv) {
    return '<li><a href="/invitation/edit?id=' + inv.id + '">' + view.prettyInvitationId(inv.id) + '</a></li>';
  }).join('\n');
  html += '</ul>';
  html += '<p class="mb-1"><strong>Reviewers:</strong></p>';
  html += '<ul style="padding-left: 15px">';
  html += conferenceStats.reviewerInvitationIds.map(function(inv) {
    return '<li><a href="/invitation/edit?id=' + inv.id + '">' + view.prettyInvitationId(inv.id) + '</a></li>';
  }).join('\n');
  html += '</ul>';
  html += '<p class="mb-1"><strong>Action Editors:</strong></p>';
  html += '<ul style="padding-left: 15px">';
  html += conferenceStats.aeInvitationIds.map(function(inv) {
    return '<li><a href="/invitation/edit?id=' + inv.id + '">' + view.prettyInvitationId(inv.id) + '</a></li>';
  }).join('\n');
  html += '</ul>';
  html += '</div>';

  html += '<div class="col-md-4 col-xs-6">';
  html += '<h4>Authors with Most Submissions:</h4>';
  html += '<table class="table table-condensed table-minimal">';
  html += '<thead><tr>' +
    '<th style="width: 35px;height: 20px;padding: 0;border: 0;">#</th>' +
    '<th style="height: 20px;padding: 0;border: 0;">Author</th>' +
    '<th style="width: 120px;height: 20px;padding: 0;border: 0;">All Submissions</th>' +
    '</tr></thead>';
  html += '<tbody>';
  html += conferenceStats.activeAuthors.map(function(entry) {
    return '<tr>' +
      '<td style="padding-left: 0;font-size: .875rem;">' + entry[1] + '</td>' +
      '<td style="padding-left: 0;font-size: .875rem;"><a href="/profile?id=' + entry[0] + '">' + view.prettyId(entry[0]) + '</a></td>' +
      '<td style="padding-left: 0;font-size: .875rem;"><a href="/search?term=' + entry[0] + '&group=' + VENUE_ID + '&content=all&source=forum">view &raquo;</a></td>' +
      '</tr>';
  }).join('\n');
  html += '</tbody>';
  html += '</table>';
  html += '</div>';

  html += '<div class="col-md-4 col-xs-6">';
  html += '<h4>Pending Editors-in-Chief Tasks:</h4>';
  html += renderCombinedTasksList(conferenceStats.incompleteEicTasks);

  html += '<h4>Overdue Tasks:</h4>';
  html += renderCombinedTasksList(conferenceStats.overdueTasks);
  html += '</div>';

  html += '</div></div>';

  $('#role-statistics').html(html);
};

var renderStatusProgress = function(data, options) {
  var assigned = data.numPapers || 0;
  var completedReviews = data.numCompletedReviews || 0;
  var pendingReviews = Math.max(assigned - completedReviews, 0);
  var rows = [
    ['Assigned', assigned],
    ['Reviews completed', completedReviews + ' / ' + assigned],
    ['Pending reviews', pendingReviews]
  ];
  if (options && options.includeDecisions) {
    var completedDecisions = data.numCompletedMetaReviews || 0;
    var pendingDecisions = Math.max(assigned - completedDecisions, 0);
    rows.push(['Decisions completed', completedDecisions + ' / ' + assigned]);
    rows.push(['Pending decisions', pendingDecisions]);
  }

  return '<table class="table table-condensed table-minimal"><tbody>' +
    rows.map(function(row) {
      return '<tr><td><strong>' + row[0] + ':</strong> ' + row[1] + '</td></tr>';
    }).join('') +
    '</tbody></table>';
};

var renderCompactStatus = function(status) {
  return '<table class="table table-condensed table-minimal"><tbody>' +
    Object.entries(status || {}).map(function(entry) {
      return '<tr><td><strong>' + _.escape(entry[0]) + ':</strong> ' + _.escape(entry[1]) + '</td></tr>';
    }).join('') +
    '</tbody></table>';
};

var renderDecisionTiming = function(data) {
  var rows = [
    ['Done <=6m', data.completedWithinSixMonths || 0],
    ['Done <=9m', data.completedWithinNineMonths || 0],
    ['Done >12m', data.completedOverTwelveMonths || 0],
    ['Pending <=6m', data.pendingWithinSixMonths || 0]
  ];
  return '<table class="table table-condensed table-minimal"><tbody>' +
    rows.map(function(row) {
      return '<tr><td><strong>' + row[0] + ':</strong> ' + row[1] + '</td></tr>';
    }).join('') +
    '</tbody></table>';
};

var renderPersonIdentity = function(summary) {
  var name = summary && summary.name || summary && summary.id || '';
  var id = summary && summary.id || '';
  var email = summary && summary.email || '';
  var profile = id
    ? '<a href="/profile?id=' + encodeURIComponent(id) + '">' + _.escape(name || id) + '</a>'
    : _.escape(name);
  var details = [];
  if (id && id !== name) {
    details.push(_.escape(view.prettyId ? view.prettyId(id) : id));
  }
  if (email) {
    details.push(_.escape(email));
  }
  return '<div class="committee-summary identity-only">' +
    '<strong>' + profile + '</strong>' +
    (details.length ? '<div class="small text-muted">' + details.join('<br>') + '</div>' : '') +
    '</div>';
};

var renderReviewerStatusTable = function(container, rows) {
  Webfield2.ui.renderTable(container, rows, {
    headings: ['#', 'Reviewer', 'Review Progress', 'Rating <span class="rating-info glyphicon glyphicon-info-sign"></span>', 'Status'],
    renders: [
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      renderPersonIdentity,
      function(data) {
        return renderStatusProgress(data);
      },
      function(data) {
        var timelinessOrder = JMLRPermissionHelpers.REVIEWER_TIMELINESS_ORDER || ['On time', 'Past due', 'Review not expected'];
        return '<table class="table table-condensed table-minimal">'
          .concat("<h4>Rating / Timeliness</h4>")
          .concat("<p class='small text-muted'>", JMLRPermissionHelpers.reviewerStatsSummary(data), "</p>")
          .concat("<tbody>")
          .concat(
            Object.entries(data.ratingsMap)
              .map(function(rating) {
                return "<tr><td class='rating'><strong>"
                  .concat(rating[0], ":</strong> ")
                  .concat(rating[1], "</td></tr>");
              })
              .join(""),
            timelinessOrder.map(function(label) {
              return "<tr><td class='rating'><strong>"
                .concat(label, ":</strong> ")
                .concat(data.timelinessMap && data.timelinessMap[label] || 0, "</td></tr>");
            }).join(""),
            "</tbody></table>"
          );
      },
      renderCompactStatus,
    ],
    sortOptions: {
      'Reviewer Name': function(row) { return row.summary.name.toLowerCase(); },
      'Assigned Papers': function(row) { return row.reviewerProgressData.numPapers; },
      'Pending Reviews': function(row) { return row.reviewerProgressData.numPapers - row.reviewerProgressData.numCompletedReviews; },
      'Reviews Submitted': function(row) { return row.reviewerProgressData.numCompletedReviews; },
      'Average Rating': function(row) { return row.ratingData.averageRating; },
      'Active Status': function(row) { return row.summary.status.Active === 'Active' ? 0 : 1; },
      'Top Reviewer': function(row) { return row.summary.status['Top Reviewer'] === 'Yes' ? 0 : 1; }
    },
    searchProperties: {
      name: ['summary.name'],
      papersAssigned: ['reviewerProgressData.numPapers'],
      averageRating:['ratingData.averageRating'],
      default: ['summary.name'],
      expertReviewer: ['summary.status.Top Reviewer'],
      active: ['summary.status.Active'],
      institutionEmail: ['summary.hasInstitutionEmail']
    },
    extraClasses: 'console-table',
    pageSize: 10,
    postRenderTable: function() {
      $(container + ' .console-table th').eq(0).css('width', '4%');
      $(container + ' .console-table th').eq(1).css('width', '26%');
      $(container + ' .console-table th').eq(2).css('width', '27%');
      $(container + ' .console-table th').eq(3).css('width', '18%');
      $(container + ' .console-table th').eq(4).css('width', '25%');
      $(container + ' td.rating').css('white-space', 'nowrap');
      $(container + ' .rating-info').on("mouseenter", function(e) {
        $(e.target).tooltip({
          title: '<strong class="tooltip-title">Rating map</strong><br/>'.concat(
            Object.entries(REVIEWER_RATING_MAP || {})
              .map(function(item) {
                return "<span>".concat(item[0], " = ").concat(item[1], "</span><br/>");
              })
              .join("")
          ),
          html: true,
          placement: "bottom"
        });
      });
    }
  });
};

var renderActionEditorStatusTable = function(container, rows) {
  Webfield2.ui.renderTable(container, rows, {
    headings: ['#', 'Action Editor', 'Review Progress', 'Decision Timing', 'Status'],
    renders: [
      function(data) {
        return '<strong class="note-number">' + data.number + '</strong>';
      },
      renderPersonIdentity,
      function(data) {
        return renderStatusProgress(data, { includeDecisions: true });
      },
      renderDecisionTiming,
      renderCompactStatus
    ],
    sortOptions: {
      'Action Editor Name': function(row) { return row.summary.name.toLowerCase(); },
      'Assigned Papers': function(row) { return row.reviewProgressData.numPapers; },
      'Pending Reviews': function(row) { return row.reviewProgressData.numPapers - row.reviewProgressData.numCompletedReviews; },
      'Reviews Completed': function(row) { return row.reviewProgressData.numCompletedReviews; },
      'Pending Decisions': function(row) { return row.reviewProgressData.numPapers - row.reviewProgressData.numCompletedMetaReviews; },
      'Decisions Completed': function(row) { return row.reviewProgressData.numCompletedMetaReviews; },
      'Decisions <=6 Months': function(row) { return row.decisionTimingData.completedWithinSixMonths; },
      'Decisions <=9 Months': function(row) { return row.decisionTimingData.completedWithinNineMonths; },
      'Decisions >12 Months': function(row) { return row.decisionTimingData.completedOverTwelveMonths; },
      'Pending <=6 Months': function(row) { return row.decisionTimingData.pendingWithinSixMonths; },
      'Active Status': function(row) { return row.summary.status.Active === 'Active' ? 0 : 1; },
      'OSS AE': function(row) { return row.summary.status['OSS AE'] === 'Yes' ? 0 : 1; }
    },
    searchProperties: {
      name: ['summary.name'],
      papersAssigned: ['reviewProgressData.numPapers'],
      active: ['summary.status.Active'],
      institutionEmail: ['summary.hasInstitutionEmail'],
      default: ['summary.name']
    },
    extraClasses: 'console-table',
    pageSize: 10,
    postRenderTable: function() {
      $(container + ' .console-table th').eq(0).css('width', '4%');
      $(container + ' .console-table th').eq(1).css('width', '24%');
      $(container + ' .console-table th').eq(2).css('width', '24%');
      $(container + ' .console-table th').eq(3).css('width', '24%');
      $(container + ' .console-table th').eq(4).css('width', '24%');
    }
  });
};
