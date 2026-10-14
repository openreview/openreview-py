// JMLR delta: Journal's EIC webfield uses invitation-prefix discovery, which
// the current API rejects. This compatibility landing keeps one compact paper
// overview and delegates workflow actions to their Journal/OpenReview owners.
(function () {
  var venue = 'JMLR';
  var eic = venue + '/Editors_In_Chief';
  var actionEditors = venue + '/Action_Editors';
  var reviewers = venue + '/Reviewers';
  var productionEditors = venue + '/Production_Editors';
  var aeAssignment = 'JMLR/Action_Editors/-/Assignment';
  var aeArchivedAssignment = 'JMLR/Action_Editors/-/Archived_Assignment';
  var aeAffinity = 'JMLR/Action_Editors/-/Affinity_Score';
  var aeRecommendation = 'JMLR/Action_Editors/-/Recommendation';
  var aeConflict = 'JMLR/Action_Editors/-/Conflict';
  var aeMaxPapers = 'JMLR/Action_Editors/-/Custom_Max_Papers';
  var aeAvailability = 'JMLR/Action_Editors/-/Assignment_Availability';
  var reviewerAssignment = 'JMLR/Reviewers/-/Assignment';
  var reviewerArchivedAssignment = 'JMLR/Reviewers/-/Archived_Assignment';
  var reviewerInviteAssignment = 'JMLR/Reviewers/-/Invite_Assignment';
  var reviewerAffinity = 'JMLR/Reviewers/-/Affinity_Score';
  var reviewerConflict = 'JMLR/Reviewers/-/Conflict';
  var reviewerPending = 'JMLR/Reviewers/-/Pending_Reviews';
  var reviewerMaxPapers = 'JMLR/Reviewers/-/Custom_Max_Papers';
  var reviewerAvailability = 'JMLR/Reviewers/-/Assignment_Availability';
  var reviewerReportInvitation = 'JMLR/Reviewers/-/Reviewer_Report';
  var submissionInvitation = venue + '/-/Submission';
  var referrer = encodeURIComponent('[JMLR EIC](/group?id=' + eic + ')');
  var aeBrowser = '/edges/browse?traverse=' + aeAssignment +
    '&edit=' + aeAssignment + ';' + aeMaxPapers + ',head:ignore;' + aeAvailability + ',head:ignore' +
    '&browse=' + aeArchivedAssignment + ';' + aeAffinity + ';' + aeRecommendation + ';' + aeConflict +
    '&version=2&referrer=' + referrer;
  var reviewerBrowser = '/edges/browse?traverse=' + reviewerAssignment +
    '&edit=' + reviewerAssignment + ';' + reviewerInviteAssignment + ';' + reviewerMaxPapers + ',head:ignore;' + reviewerAvailability + ',head:ignore' +
    '&browse=' + reviewerArchivedAssignment + ';' + reviewerAffinity + ';' + reviewerConflict + ';' + reviewerPending + ',head:ignore' +
    '&version=2&filter=' + encodeURIComponent(reviewerPending + ' == 0 AND ' + reviewerAvailability + ' == Available AND ' + reviewerConflict + ' == 0') +
    '&referrer=' + referrer;
  var recruitmentUrl = '/forum?id={{PROD_JOURNAL_ID}}&referrer=' + referrer;
  var reviewerReportUrl = '/invitation?id=' + encodeURIComponent(reviewerReportInvitation);
  var escapeHtml = function (value) {
    return $('<div>').text(value == null ? '' : String(value)).html();
  };

  var fieldValue = function (field) {
    return field && Object.prototype.hasOwnProperty.call(field, 'value') ? field.value : field;
  };

  var activeEdgesByHead = function (edges) {
    return (edges || []).reduce(function (byHead, edge) {
      if (!edge || edge.ddate || !edge.head) return byHead;
      byHead[edge.head] = byHead[edge.head] || [];
      byHead[edge.head].push(edge);
      return byHead;
    }, {});
  };

  var currentProfileId = function () {
    return user && user.profile && user.profile.id || user && user.id || '';
  };

  var isAuthoredByCurrentEic = function (submission) {
    var authorIds = fieldValue(submission.content && submission.content.authorids) || [];
    return Array.isArray(authorIds) && authorIds.indexOf(currentProfileId()) >= 0;
  };

  var stageFor = function (submission) {
    var venueId = fieldValue(submission.content && submission.content.venueid) || '';
    if (venueId === venue + '/Submitted' || venueId === venue + '/Assigning_AE' || venueId === venue + '/Assigned_AE') return 'Submitted';
    if (venueId === venue + '/Under_Review') return 'Under Review';
    if (venueId.indexOf(venue + '/Camera_Ready_') === 0 || venueId === venue + '/Publication_Retracted') return 'Camera Ready';
    if (venueId === venue || venueId === venue + '/Rejected' || venueId === venue + '/Desk_Rejected' ||
        venueId === venue + '/Decision_Pending' || venueId === venue + '/Retracted_Acceptance') return 'Decision Made';
    return 'Other';
  };

  var reviewCount = function (submission) {
    var details = submission.details || {};
    var replies = details.directReplies || details.replies || [];
    return replies.filter(function (reply) {
      return (reply.invitations || []).some(function (id) { return /\/-\/Review$/.test(id); });
    }).length;
  };

  var paperAssignmentUrl = function (submission, invitation) {
    return '/edges/browse?start=' + encodeURIComponent('staticList,type:head,ids:' + submission.id) +
      '&traverse=' + invitation + '&edit=' + invitation + '&version=2&referrer=' + referrer;
  };

  var paperRow = function (submission, aeByHead, reviewersByHead) {
    var number = submission.number;
    var title = fieldValue(submission.content && submission.content.title) || 'Untitled submission';
    var stage = stageFor(submission);
    var assignedAes = (aeByHead[submission.id] || []).map(function (edge) { return edge.tail; });
    var assignedReviewers = (reviewersByHead[submission.id] || []).map(function (edge) { return edge.tail; });
    var aeText = assignedAes.length ? assignedAes.join(', ') : 'Unassigned';
    var searchText = [number, title, stage, aeText].concat(assignedReviewers).join(' ').toLowerCase();
    var actions = [
      '<a href="/forum?id=' + encodeURIComponent(submission.id) + '&referrer=' + referrer + '">Open paper</a>',
      '<a href="' + paperAssignmentUrl(submission, aeAssignment) + '">Edit AE</a>'
    ];
    if (stage === 'Under Review') {
      actions.push('<a href="/invitation?id=' + encodeURIComponent(venue + '/Paper' + number + '/Reviewers/-/Assignment') +
        '&referrer=' + referrer + '">Edit reviewers</a>');
    }
    return '<tr data-stage="' + escapeHtml(stage) + '" data-search="' + escapeHtml(searchText) + '">' +
      '<td>' + escapeHtml(number) + '</td><td><strong>' + escapeHtml(title) + '</strong></td>' +
      '<td>' + escapeHtml(stage) + '</td><td>' + escapeHtml(aeText) + '</td>' +
      '<td>' + assignedReviewers.length + ' assigned / ' + reviewCount(submission) + ' submitted</td>' +
      '<td>' + actions.join(' &middot; ') + '</td></tr>';
  };

  var taskNames = {
    'Desk_Rejection_Approval': 'Review desk rejection',
    'Decision_Approval': 'Review decision',
    'Retraction_Approval': 'Review retraction'
  };

  var renderPendingTasks = function (submissions, invitations) {
    var tasks = [];
    var submissionsByNumber = (submissions || []).reduce(function (result, submission) {
      result[String(submission.number)] = submission;
      return result;
    }, {});
    (invitations || []).forEach(function (invitation) {
      var invitationId = invitation && invitation.id || '';
      var match = invitationId.match(/^JMLR\/Paper(\d+)\/-\/(Desk_Rejection_Approval|Decision_Approval|Retraction_Approval)$/);
      if (!match || !submissionsByNumber[match[1]]) return;
      var submission = submissionsByNumber[match[1]];
      var replies = submission.details && (submission.details.directReplies || submission.details.replies) || [];
      var alreadyCompleted = replies.some(function (reply) {
        return (reply.invitations || []).indexOf(invitationId) >= 0;
      });
      if (!alreadyCompleted) tasks.push({
        submission: submission,
        invitationId: invitationId,
        label: taskNames[match[2]]
      });
    });
    if (!tasks.length) {
      $('#pending-tasks').html('<div class="container"><p class="text-muted">No Editors-in-Chief tasks require action. Normal Action Editor matching and deployment run automatically.</p></div>');
      return;
    }
    $('#pending-tasks').html('<div class="container"><ul class="list-unstyled submissions-list task-list">' +
      tasks.map(function (task) {
        var title = fieldValue(task.submission.content && task.submission.content.title) || 'Untitled submission';
        return '<li class="note"><strong><a href="/forum?id=' + encodeURIComponent(task.submission.id) + '&referrer=' + referrer + '">' +
          escapeHtml(task.label) + '</a></strong><p class="mb-0">Paper ' + escapeHtml(task.submission.number) + ': ' + escapeHtml(title) + '</p></li>';
      }).join('') + '</ul></div>');
  };

  var renderAllSubmissions = function (submissions, aeEdges, reviewerEdges) {
    var aeByHead = activeEdgesByHead(aeEdges);
    var reviewersByHead = activeEdgesByHead(reviewerEdges);
    var sorted = (submissions || []).slice().sort(function (left, right) { return right.number - left.number; });
    var rows = sorted.map(function (submission) { return paperRow(submission, aeByHead, reviewersByHead); }).join('');
    $('#all-submissions').html(
      '<div class="container-fluid"><div class="row" style="margin-bottom: 12px;">' +
      '<div class="col-sm-7"><label for="jmlr-assignment-search">Search submissions</label>' +
      '<input id="jmlr-assignment-search" class="form-control" type="search" placeholder="Paper number, title, editor, or reviewer"></div>' +
      '<div class="col-sm-4"><label for="jmlr-stage-filter">Stage</label><select id="jmlr-stage-filter" class="form-control">' +
      ['All', 'Submitted', 'Under Review', 'Decision Made', 'Camera Ready', 'Other'].map(function (stage) {
        return '<option value="' + escapeHtml(stage) + '">' + escapeHtml(stage) + '</option>';
      }).join('') + '</select></div></div>' +
      '<style>.jmlr-eic-table th,.jmlr-eic-table td,.jmlr-eic-table a{white-space:normal;overflow-wrap: anywhere;word-break:break-word;vertical-align:top;}</style>' +
      '<p id="jmlr-assignment-count" class="text-muted"></p><div class="table-responsive"><table class="table table-striped console-table jmlr-eic-table" style="width: 100%; min-width: 850px; table-layout: fixed;">' +
      '<colgroup><col style="width:5%"><col style="width:25%"><col style="width:15%"><col style="width:20%"><col style="width:17%"><col style="width:18%"></colgroup>' +
      '<thead><tr><th>#</th><th>Paper</th><th>Stage</th><th>Action Editor</th><th>Review progress</th><th>Actions</th></tr></thead>' +
      '<tbody>' + rows + '</tbody></table></div></div>');
    var applyFilters = function () {
      var query = String($('#jmlr-assignment-search').val() || '').toLowerCase().trim();
      var stage = $('#jmlr-stage-filter').val();
      var visible = 0;
      $('#all-submissions tbody tr').each(function () {
        var row = $(this);
        var matches = (!query || String(row.attr('data-search') || '').indexOf(query) >= 0) &&
          (stage === 'All' || row.attr('data-stage') === stage);
        row.toggle(matches);
        if (matches) visible += 1;
      });
      $('#jmlr-assignment-count').text(visible + ' assignment row' + (visible === 1 ? '' : 's'));
    };
    $('#jmlr-assignment-search').on('input', applyFilters);
    $('#jmlr-stage-filter').on('change', applyFilters);
    applyFilters();
  };

  var linkList = function (items) {
    return '<div class="container"><ul class="list-unstyled submissions-list task-list">' + items.map(function (item) {
      return '<li class="note"><p class="mb-1"><strong><a href="' + item[1] + '">' + escapeHtml(item[0]) + '</a></strong></p></li>';
    }).join('') + '</ul></div>';
  };

  var renderNavigationTabs = function () {
    $('#assignments').html(linkList([['Action Editor assignment browser', aeBrowser], ['Reviewer assignment browser', reviewerBrowser]]));
    $('#recruitment').html(linkList([['Recruit Action Editors or Reviewers', recruitmentUrl], ['Reviewer Report', reviewerReportUrl]]));
    $('#role-management').html(linkList([
      ['Manage Action Editors and track eligibility', '/invitation?id=JMLR%2F-%2FManage_Action_Editors'],
      ['Manage Tracks', '/invitation?id=JMLR%2F-%2FManage_Tracks'],
      ['Manage Action Editor availability', '/group?id=' + encodeURIComponent(actionEditors)],
      ['Edit Editors-in-Chief', '/group/edit?id=' + encodeURIComponent(eic)],
      ['Edit Reviewers', '/group/edit?id=' + encodeURIComponent(reviewers)],
      ['Edit Production Editors', '/group/edit?id=' + encodeURIComponent(productionEditors)],
      ['Production Editor worklist', '/group?id=' + encodeURIComponent(productionEditors)]
    ]));
  };

  var renderLoadFailure = function () {
    var message = "{{MESSAGE_TEMPLATE_JSON:eic/assignment_overview_load_failure.html}}";
    $('#pending-tasks, #all-submissions').html(message);
    Webfield2.ui.done();
  };

  Webfield2.ui.setup('#group-container', venue, {
    title: 'JMLR Editors-in-Chief Console',
    instructions: 'Inspect journal assignments and open the standard Journal or OpenReview page that owns each action.',
    tabs: ['Pending Tasks', 'All Submissions', 'Assignments', 'Recruitment', 'Role Management'],
    referrer: typeof args !== 'undefined' && args ? args.referrer : undefined,
    fullWidth: true
  });

  if (!user || user.isGuest) {
    Webfield2.ui.errorMessage('You must be logged in to access this page.');
    Webfield2.ui.done();
    return;
  }

  renderNavigationTabs();
  $.when(
    Webfield2.api.getAllSubmissions(submissionInvitation, { domain: venue }),
    Webfield2.api.get('/invitations', {
      invitee: eic, domain: venue, expired: false, select: 'id', stream: true
    }).then(function (result) { return result.invitations || []; }),
    Webfield2.api.get('/edges', { invitation: aeAssignment, domain: venue, stream: true }).then(function (result) { return result.edges || []; }),
    Webfield2.api.get('/edges', { invitation: reviewerAssignment, domain: venue, stream: true }).then(function (result) { return result.edges || []; })
  ).then(function (submissions, taskInvitations, aeEdges, reviewerEdges) {
    var visibleSubmissions = (submissions || []).filter(function (submission) { return !isAuthoredByCurrentEic(submission); });
    renderPendingTasks(visibleSubmissions, taskInvitations);
    renderAllSubmissions(visibleSubmissions, aeEdges, reviewerEdges);
    Webfield2.ui.done();
  }, renderLoadFailure);
}());
