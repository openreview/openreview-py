// JMLR delta: Journal owns the browser; this adds prior-round context and a
// checked assignment action for load-exempt continuity reviewers.
(function (root, factory) {
  var redirects = factory();
  if (typeof module === 'object' && module.exports) module.exports = redirects;
  if (root) root.JMLRPreviousReviewerRedirects = redirects;
}(typeof globalThis === 'undefined' ? this : globalThis, function () {
  'use strict';

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function continuityAssignmentEdge(config, reviewerId) {
    var required = [
      config && config.venueId,
      config && config.submissionId,
      config && config.assignmentInvitationId,
      config && config.paperActionEditorsId,
      config && config.paperActionEditorSignatureId,
      config && config.paperAuthorsId
    ];
    if (required.some(function (value) { return typeof value !== 'string' || !value; }) ||
        typeof reviewerId !== 'string' || !/^~[^\s/]*\d+$/.test(reviewerId)) {
      throw new Error('The prior-reviewer assignment context is incomplete.');
    }
    return {
      invitation: config.assignmentInvitationId,
      signatures: [config.paperActionEditorSignatureId],
      readers: [config.venueId, config.paperActionEditorsId, reviewerId],
      nonreaders: [config.paperAuthorsId],
      writers: [config.venueId, config.paperActionEditorsId],
      head: config.submissionId,
      tail: reviewerId,
      weight: 1
    };
  }

  function assignmentErrorMessage(error) {
    return typeof error === 'string' && error ||
      error && error.responseJSON && error.responseJSON.message ||
      error && error.message || 'The previous reviewer could not be assigned.';
  }

  function refreshAssignmentState(config, api) {
    if (!config || !config.assignmentInvitationId || !config.submissionId ||
        !api || typeof api.get !== 'function') return Promise.resolve(config);
    return api.get('/edges', {
      invitation: config.assignmentInvitationId,
      head: config.submissionId
    }).then(function (result) {
      var assigned = {};
      (result && result.edges || []).forEach(function (edge) {
        if (!edge.ddate && typeof edge.tail === 'string') assigned[edge.tail] = true;
      });
      (config.reviewers || []).forEach(function (reviewer) {
        reviewer.assigned = assigned[reviewer.id] === true;
      });
      return config;
    });
  }

  function waitForAssignment(config, reviewerId, api, attempts) {
    return refreshAssignmentState(config, api).then(function (current) {
      var assigned = (current.reviewers || []).some(function (reviewer) {
        return reviewer.id === reviewerId && reviewer.assigned === true;
      });
      if (assigned) return current;
      if (attempts <= 0) throw new Error(
        'The assignment is still processing. Refresh before retrying.'
      );
      return new Promise(function (resolve) { setTimeout(resolve, 1000); })
        .then(function () {
          return waitForAssignment(config, reviewerId, api, attempts - 1);
        });
    });
  }

  function renderWithUrl(config, browseUrl, origin) {
    var browseHref = escapeHtml(browseUrl);
    var reviewers = config && config.reviewers || [];
    var previousForumId = config && config.previousForumId;
    var previous = '';
    if (typeof previousForumId === 'string' && previousForumId && previousForumId.trim() === previousForumId) {
      var previousHref = escapeHtml(origin + '/forum?id=' + encodeURIComponent(previousForumId));
      previous = '<section class="jmlr-previous-reviewers">' +
        (reviewers.length
          ? '<h3>Previous reviewers</h3><ul class="jmlr-previous-reviewer-names">' +
            reviewers.map(function (reviewer) {
              var assigned = reviewer.assigned === true;
              return '<li><span class="jmlr-previous-reviewer-name">' +
                escapeHtml(reviewer.displayName) + '</span> ' +
                '<button type="button" class="btn btn-sm btn-primary jmlr-assign-previous-reviewer" ' +
                'data-reviewer-id="' + escapeHtml(reviewer.id) + '"' +
                (assigned ? ' disabled aria-disabled="true"' : '') + '>' +
                (assigned ? 'Assigned' : 'Assign previous reviewer') + '</button> ' +
                '<span class="jmlr-previous-reviewer-status' +
                (assigned ? ' text-success' : '') + '" aria-live="polite">' +
                (assigned ? ' Previous reviewer assigned.' : '') + '</span></li>';
            }).join('') + '</ul>'
          : '') +
        '<p>OpenReview permissions determine whether you can view the previous paper and its reviews.</p>' +
        '<p><a class="jmlr-view-previous-paper" href="' + previousHref +
        '">View previous paper and its reviews</a></p></section>';
    }
    return previous + '<p class="text-center"><a href="' + browseHref +
      '" class="btn btn-lg btn-primary jmlr-browse-all-reviewers">Browse all reviewers</a></p>';
  }

  function render(config, edgeBrowserParams, actorId, origin) {
    var params = edgeBrowserParams.replace('{userId}', actorId);
    var browseUrl = origin + '/edges/browse?' + params;
    return renderWithUrl(config, browseUrl, origin);
  }

  function bindAssignmentAction(config) {
    $('#notes').off('click.jmlrPreviousReviewer')
      .on('click.jmlrPreviousReviewer', '.jmlr-assign-previous-reviewer', function () {
        var button = $(this);
        if (button.prop('disabled')) return;
        var status = button.siblings('.jmlr-previous-reviewer-status');
        var edge;
        try {
          edge = continuityAssignmentEdge(config, button.attr('data-reviewer-id'));
        } catch (error) {
          status.addClass('text-danger').text(assignmentErrorMessage(error));
          return;
        }
        button.prop('disabled', true);
        status.removeClass('text-danger text-success').text('Assigning...');
        Webfield2.api.post('/edges', edge).then(function () {
          return waitForAssignment(config, edge.tail, Webfield2.api, 120);
        }).then(function () {
          button.text('Assigned');
          status.addClass('text-success').text(' Previous reviewer assigned.');
        }, function (error) {
          button.prop('disabled', false);
          status.addClass('text-danger').text(' ' + assignmentErrorMessage(error));
        });
      });
  }

  function install(config) {
    if (typeof window === 'undefined' || typeof $ === 'undefined') return;
    var liveConfig = config;
    load = function () {
      return refreshAssignmentState(liveConfig, Webfield2.api).then(function (current) {
        liveConfig = current;
        return liveConfig;
      });
    };
    renderContent = function () {
      var params = EDGE_BROWSER_PARAMS.replace('{userId}', user.profile.id);
      var browseUrl = location.origin + '/edges/browse?' + params;
      $('#content').removeClass('legacy-styles');
      $('#notes').empty().append(renderWithUrl(liveConfig, browseUrl, location.origin));
      bindAssignmentAction(liveConfig);
      return $.Deferred().resolve();
    };
  }

  return {
    assignmentErrorMessage: assignmentErrorMessage,
    refreshAssignmentState: refreshAssignmentState,
    waitForAssignment: waitForAssignment,
    continuityAssignmentEdge: continuityAssignmentEdge,
    escapeHtml: escapeHtml,
    install: install,
    render: render,
    renderWithUrl: renderWithUrl
  };
}));
