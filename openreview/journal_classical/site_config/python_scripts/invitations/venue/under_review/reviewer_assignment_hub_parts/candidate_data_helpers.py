REVIEWER_CANDIDATE_DATA_HELPERS_JS = r"""    function getReviewerCandidateTails() {
      var configuredReviewerTails = _.uniq((AUTO_ASSIGN_CONFIG.reviewerCandidateTails || []).filter(function(tail) {
    return !!tail && tail.charAt(0) === '~';
      }));
      var edgeRequests = [
    Webfield2.api.getAll('/edges', { invitation: AUTO_ASSIGN_CONFIG.reviewersAffinityScoreId, head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId, stream: true }),
    Webfield2.api.getAll('/edges', { invitation: AUTO_ASSIGN_CONFIG.reviewersPendingReviewsId, domain: AUTO_ASSIGN_CONFIG.venueId, stream: true }),
    Webfield2.api.getAll('/edges', { invitation: AUTO_ASSIGN_CONFIG.reviewersCustomMaxPapersId, domain: AUTO_ASSIGN_CONFIG.venueId, stream: true })
      ];
      return $.when.apply($, edgeRequests).then(function(affinityEdges, pendingEdges, maxPapersEdges) {
    var availabilityTails = Object.keys(AUTO_ASSIGN_CONFIG.reviewerAssignmentAvailability || {});
    var edgeTails = [].concat(affinityEdges || [], pendingEdges || [], maxPapersEdges || []).map(function(edge) {
      return edge.tail;
    }).concat(availabilityTails).concat(configuredReviewerTails);
    return _.uniq(edgeTails.filter(function(tail) {
      return !!tail && tail.charAt(0) === '~';
    }));
      }, function() {
    return configuredReviewerTails;
      });
    }

    function getProfilesById(ids) {
      var profileIds = _.uniq((ids || []).filter(function(id) { return id && (id.charAt(0) === '~' || id.indexOf('@') >= 0); }));
      var requests = profileIds.map(function(id) {
    var request = id.charAt(0) === '~'
      ? Webfield2.api.get('/profiles', { id: id })
      : Webfield2.api.post('/profiles/search', { ids: [id] });
    return request.then(function(result) {
      var profile = result && result.profile || result && result.profiles && result.profiles[0] || result;
      return { id: id, profile: profile || null };
    }, function() {
      return { id: id, profile: null };
    });
      });
      if (!requests.length) return $.Deferred().resolve({}).promise();
      return $.when.apply($, requests).then(function() {
    var results = requests.length === 1 ? [arguments[0]] : Array.prototype.slice.call(arguments);
    return results.reduce(function(byId, result) {
      byId[result.id] = result.profile;
      return byId;
    }, {});
      });
    }

    function getExpertReviewerIds() {
      return Webfield2.api.get('/groups', { id: AUTO_ASSIGN_CONFIG.expertReviewersId }).then(function(result) {
    var group = result && result.groups && result.groups[0] || result && result.group || result;
    return new Set((group && group.members || []).filter(function(member) { return !!member; }));
      }, function() {
    return new Set();
      });
    }

    function getProfileName(profile, fallback) {
      if (!profile) return fallback;
      var content = profile.content || {};
      if (content.preferredName) return content.preferredName;
      if (content.names && content.names.length) {
    var name = content.names[0] || {};
    if (name.fullname) return name.fullname;
    return [name.first, name.middle, name.last].filter(function(part) { return !!part; }).join(' ') || fallback;
      }
      return fallback;
    }

    function getProfileEmails(profile, fallback) {
      if (!profile) return fallback && fallback.indexOf('@') >= 0 ? fallback : '';
      var content = profile.content || {};
      var emails = (content.emails || []).concat(content.preferredEmail ? [content.preferredEmail] : []);
      emails = _.uniq(emails.filter(function(email) { return !!email && email.indexOf('*') < 0; }));
      return emails[0] || (fallback && fallback.indexOf('@') >= 0 ? fallback : '');
    }

    function getProfileSearchEmails(profile, fallback) {
      if (!profile) return fallback && fallback.indexOf('@') >= 0 ? fallback : '';
      var content = profile.content || {};
      var emails = (content.emails || []).concat(content.preferredEmail ? [content.preferredEmail] : []);
      emails = _.uniq(emails.filter(function(email) { return !!email; }));
      return emails.join(' ') || (fallback && fallback.indexOf('@') >= 0 ? fallback : '');
    }

    function getProfileAffiliation(profile) {
      var content = profile && profile.content || {};
      var history = content.history || [];
      if (!history.length) return '';
      var affiliation = history[0] || {};
      return affiliation.institution && affiliation.institution.name || affiliation.position || '';
    }

    function getEdgesByTail(invitationId, head, tails) {
      var requests = tails.map(function(tail) {
    var params = { invitation: invitationId, tail: tail, domain: AUTO_ASSIGN_CONFIG.venueId };
    if (head) params.head = head;
    return Webfield2.api.getAll('/edges', params).then(function(edges) {
      return { tail: tail, edges: edges || [] };
    });
      });
      if (!requests.length) return $.Deferred().resolve({}).promise();
      return $.when.apply($, requests).then(function() {
    var results = requests.length === 1 ? [arguments[0]] : Array.prototype.slice.call(arguments);
    return results.reduce(function(byTail, result) {
      byTail[result.tail] = result.edges;
      return byTail;
    }, {});
      });
    }

    function getReviewerAssignmentHistoryByTail(tails) {
      var requests = tails.map(function(tail) {
    return Webfield2.api.getAll('/edges', { tail: tail, domain: AUTO_ASSIGN_CONFIG.venueId, stream: true, trash: true }).then(function(edges) {
      return {
        tail: tail,
        edges: (edges || []).filter(function(edge) {
          return edge && edge.invitation && /\/Reviewers\/-\/Assignment$/.test(edge.invitation);
        })
      };
    });
      });
      if (!requests.length) return $.Deferred().resolve({}).promise();
      return $.when.apply($, requests).then(function() {
    var results = requests.length === 1 ? [arguments[0]] : Array.prototype.slice.call(arguments);
    return results.reduce(function(byTail, result) {
      byTail[result.tail] = result.edges;
      return byTail;
    }, {});
      });
    }

    function activeReviewerDueDateEdgesByTail(edges) {
      return (edges || []).filter(function(edge) {
    return edge && edge.tail && !edge.ddate;
      }).reduce(function(byTail, edge) {
    var existing = byTail[edge.tail];
    var existingTime = existing && (existing.tcdate || existing.cdate || 0) || 0;
    var edgeTime = edge.tcdate || edge.cdate || 0;
    if (!existing || edgeTime >= existingTime) byTail[edge.tail] = edge;
    return byTail;
      }, {});
    }

    function reviewerDueDateEdgeMillis(edge) {
      if (!edge || edge.weight === undefined || edge.weight === null) return null;
      var dueDateMillis = Number(edge.weight);
      return isNaN(dueDateMillis) ? null : dueDateMillis;
    }

    function reviewerAssignmentDueDateMillis(assignmentEdge, dueDateEdge) {
      var storedDueDate = reviewerDueDateEdgeMillis(dueDateEdge);
      if (storedDueDate) return storedDueDate;
      if (!assignmentEdge) return null;
      if (assignmentEdge.cdate && AUTO_ASSIGN_CONFIG.reviewPeriodDays) {
        return Number(assignmentEdge.cdate) + (Number(AUTO_ASSIGN_CONFIG.reviewPeriodDays) * 24 * 60 * 60 * 1000);
      }
      return null;
    }

    function reviewerAssignmentDueDateText(assignmentEdge, dueDateEdge) {
      var dueDateMillis = reviewerAssignmentDueDateMillis(assignmentEdge, dueDateEdge);
      if (!dueDateMillis || isNaN(dueDateMillis)) return 'Unknown';
      return formatAutoAssignDate(dueDateMillis);
    }

    function renderReviewerStatusArea() {
      return withAutoAssignTimeout($.when(
    Webfield2.api.getAll('/edges', { invitation: reviewerAssignmentInvitationId(), head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId, trash: true, stream: true }),
    Webfield2.api.getAll('/edges', { invitation: AUTO_ASSIGN_CONFIG.reviewersInviteAssignmentId, head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId, trash: true, stream: true }),
    Webfield2.api.getAll('/edges', { invitation: AUTO_ASSIGN_CONFIG.reviewersReviewDueDateId, head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId, trash: true, stream: true })
      ), 45000, 'Timed out refreshing reviewer assignment status. Reload the assignment page to check current reviewers.').then(function(assignmentEdges, inviteEdges, dueDateEdges) {
    assignmentEdges = assignmentEdges || [];
    inviteEdges = inviteEdges || [];
    dueDateEdges = dueDateEdges || [];
    var activeAssignments = assignmentEdges.filter(function(edge) { return !edge.ddate; });
    var dueDateByTail = activeReviewerDueDateEdgesByTail(dueDateEdges);
    var assignmentByTail = activeAssignments.reduce(function(byTail, edge) {
      if (edge.tail) byTail[edge.tail] = edge;
      return byTail;
    }, {});
    var rows = [];
    activeAssignments.forEach(function(edge) {
      rows.push({
        reviewer: edge.tail,
        source: 'Reviewer assignment',
        status: 'Assigned',
        assignmentEdge: edge
      });
    });
    inviteEdges.forEach(function(edge) {
      if (edge.tail && edge.tail.charAt(0) === '~') return;
      var normalizedStatus = normalizeInviteStatus(edge, assignmentByTail);
      if (assignmentByTail[edge.tail] && normalizedStatus === 'Assigned') return;
      rows.push({
        reviewer: edge.tail,
        source: 'External invitation',
        status: normalizedStatus
      });
    });
    return $.when(
      getReviewerStatsByTail(rows.map(function(row) { return row.reviewer; })),
      getProfilesById(rows.map(function(row) { return row.reviewer; }))
    ).then(function(statsByTail, profilesById) {
      var tableRows = rows.length ? rows.map(function(row) {
        var stats = row.reviewer && row.reviewer.charAt(0) === '~' ? statsByTail[row.reviewer] : unavailableReviewerStats('external invitation not linked to a reviewer profile');
        var profile = profilesById[row.reviewer] || null;
        var profileId = profile && profile.id || row.reviewer;
        var isExternalInvitation = row.source === 'External invitation';
        var reviewerName = getProfileName(profile, '');
        var reviewerEmail = getProfileEmails(profile, row.reviewer && row.reviewer.indexOf('@') >= 0 ? row.reviewer : '');
        var reviewerAffiliation = getProfileAffiliation(profile);
        var reviewerLabel = isExternalInvitation ? row.reviewer : reviewerContinuityLabelForTail(row.reviewer, reviewerName || reviewerEmail || row.reviewer);
        var reviewerDetail = !isExternalInvitation && reviewerName && reviewerEmail ? '<br><span class="text-muted">' + escapeAutoAssignHtml(reviewerEmail) + '</span>' : '';
        var reviewerCell = profileId && profileId.charAt(0) === '~'
          ? '<a href="/profile?id=' + encodeURIComponent(profileId) + '" target="_blank" rel="noopener noreferrer" title="' + escapeAutoAssignHtml(profileId) + '">' + escapeAutoAssignHtml(reviewerLabel) + '</a>' + reviewerDetail
          : escapeAutoAssignHtml(row.reviewer);
        var assignmentEdge = row.assignmentEdge || {};
        var removeCell = row.source === 'Reviewer assignment' && row.status === 'Assigned' && assignmentEdge.id
          ? '<input type="checkbox" class="remove-assigned-reviewer" value="' + escapeAutoAssignHtml(assignmentEdge.id) + '" data-reviewer-tail="' + escapeAutoAssignHtml(row.reviewer || '') + '" data-assignment-invitation="' + escapeAutoAssignHtml(assignmentEdge.invitation || reviewerAssignmentInvitationId()) + '" data-assignment-weight="' + escapeAutoAssignHtml(assignmentEdge.weight === undefined ? 1 : assignmentEdge.weight) + '" data-assignment-label="' + escapeAutoAssignHtml(assignmentEdge.label || '') + '" aria-label="Remove ' + escapeAutoAssignHtml(row.reviewer || '') + '">'
          : '';
        var reviewDueDateCell = row.assignmentEdge
          ? escapeAutoAssignHtml(reviewerAssignmentDueDateText(row.assignmentEdge, dueDateByTail[row.reviewer]))
          : '<span class="text-muted">After acceptance</span>';
        return '<tr>' +
          '<td style="width: 220px; max-width: 220px; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">' + reviewerCell + '</td>' +
          '<td style="white-space: normal; overflow-wrap: anywhere;">' + escapeAutoAssignHtml(reviewerName || reviewerEmail || '') + '</td>' +
          '<td style="white-space: normal; overflow-wrap: anywhere;">' + escapeAutoAssignHtml(reviewerAffiliation || '') + '</td>' +
          '<td style="white-space: normal; overflow-wrap: anywhere;">' + escapeAutoAssignHtml(reviewerStatsSummary(stats)) + '</td>' +
          '<td style="width: 120px; min-width: 120px; white-space: nowrap;">' + reviewDueDateCell + '</td>' +
          '<td style="width: 64px; min-width: 64px; text-align: center;">' + removeCell + '</td>' +
          '</tr>';
      }).join('') : '<tr><td colspan="6" class="text-muted">No reviewers or external invitations yet.</td></tr>';
      $('#reviewer-assignment-status').html(
        '<div class="panel panel-default" style="max-width: 1100px; margin: 12px auto; text-align: left;">' +
          '<div class="panel-heading"><strong>Reviewer assignment status</strong></div>' +
          requiredReviewerCountControlHtml(activeAssignments.length) +
          '<table class="table table-condensed" style="margin-bottom: 0; table-layout: fixed;">' +
            '<thead><tr><th style="width: 220px; max-width: 220px;">Reviewer / Invitee</th><th>Name</th><th>Institution</th><th>Rating / Timeliness</th><th style="width: 120px; min-width: 120px;">Review Due Date</th><th style="width: 64px; min-width: 64px; text-align: center;">Remove</th></tr></thead>' +
            '<tbody>' + tableRows + '</tbody>' +
          '</table>' +
          '<div class="panel-footer">' +
            '<button id="remove-selected-reviewers" class="btn btn-xs btn-danger" type="button">Remove selected reviewers</button>' +
            '<span id="remove-selected-reviewers-status" style="margin-left: 8px;"></span>' +
          '</div>' +
        '</div>'
      );
      $('#required-reviewers-count').attr('data-active-assignments', activeAssignments.length);
      $('#save-required-reviewers-count').off('click.requiredReviewers').on('click.requiredReviewers', saveRequiredReviewerCount);
      $('#remove-selected-reviewers').off('click.removeReviewers').on('click.removeReviewers', removeSelectedAssignedReviewers);
      return { activeAssignments: activeAssignments, inviteEdges: inviteEdges };
    });
      });
    }

    function setRemoveSelectedReviewersStatus(message, isError) {
      $('#remove-selected-reviewers-status')
    .text(message || '')
    .toggleClass('text-danger', !!isError)
    .toggleClass('text-success', !isError && !!message);
    }

    function waitForReviewerRemovalReadback(removedReviewerTails, options) {
      var removedTails = _.uniq((removedReviewerTails || []).filter(function(tail) { return !!tail; }));
      options = options || {};
      var maxAttempts = options.maxAttempts || 30;
      var delayMillis = options.delayMillis || 2000;
      var attempt = 0;

      var readOnce = function() {
    return withAutoAssignTimeout($.when(
      Webfield2.api.getAll('/edges', {
        invitation: reviewerAssignmentInvitationId(),
        head: AUTO_ASSIGN_CONFIG.noteId,
        domain: AUTO_ASSIGN_CONFIG.venueId,
        trash: true,
        stream: true
      }),
      Webfield2.api.getGroup(getPaperReviewersGroupId(), { select: 'id,members' })
    ), 45000, 'Timed out verifying reviewer removal readback. Reload the assignment page to check whether the reviewer was removed.').then(function(edges, group) {
      var activeEdgeTails = _.uniq((edges || []).filter(function(edge) { return !edge.ddate; }).map(function(edge) { return edge.tail; }));
      var groupMembers = _.uniq((group && group.members || []).filter(function(member) { return !!member; }));
      var stillActiveEdgeTails = removedTails.filter(function(tail) { return activeEdgeTails.indexOf(tail) >= 0; });
      var stillGroupTails = removedTails.filter(function(tail) { return groupMembers.indexOf(tail) >= 0; });
      return {
        ok: !stillActiveEdgeTails.length && !stillGroupTails.length,
        activeEdgeTails: activeEdgeTails,
        groupMembers: groupMembers,
        stillActiveEdgeTails: stillActiveEdgeTails,
        stillGroupTails: stillGroupTails
      };
    });
      };

      var retry = function() {
    attempt += 1;
    return readOnce().then(function(readback) {
      if (readback.ok) return readback;
      if (options.onProgress) options.onProgress(attempt, maxAttempts, readback);
      if (attempt >= maxAttempts) {
        var stillPresent = _.uniq(readback.stillActiveEdgeTails.concat(readback.stillGroupTails));
        return $.Deferred().reject({
          message: 'Reviewer removal submitted, but checked readback still found assignment edge or paper reviewer group membership for: ' + stillPresent.join(', ') + ' after ' + attempt + ' readback attempts.',
          readback: readback
        }).promise();
      }
      return new Promise(function(resolve, reject) {
        setTimeout(function() {
          retry().then(resolve, reject);
        }, delayMillis);
      });
    });
      };

      if (!removedTails.length) return $.Deferred().resolve({ ok: true, activeEdgeTails: [], groupMembers: [] }).promise();
      return retry();
    }

    function removeSelectedAssignedReviewers() {
      var selectedAssignments = $('.remove-assigned-reviewer:checked').map(function() {
    var checkbox = $(this);
    return {
      edgeId: checkbox.val(),
      reviewer: checkbox.attr('data-reviewer-tail'),
      invitation: checkbox.attr('data-assignment-invitation') || reviewerAssignmentInvitationId(),
      weight: Number(checkbox.attr('data-assignment-weight') || 1),
      label: checkbox.attr('data-assignment-label') || ''
    };
      }).get();
      var button = $('#remove-selected-reviewers');
      if (!selectedAssignments.length) {
    setRemoveSelectedReviewersStatus('Select at least one reviewer to remove.', true);
    return;
      }
      button.prop('disabled', true).text('Removing...');
      setRemoveSelectedReviewersStatus('Removing ' + selectedAssignments.length + ' reviewer(s)...', false);
      getAutoAssignmentSignature().then(function(signature) {
    var chain = $.Deferred().resolve().promise();
    selectedAssignments.forEach(function(assignment) {
      chain = chain.then(function() {
        var payload = {
          id: assignment.edgeId,
          invitation: assignment.invitation,
          signatures: [signature],
          head: AUTO_ASSIGN_CONFIG.noteId,
          tail: assignment.reviewer,
          weight: assignment.weight || 1,
          ddate: Date.now()
        };
        if (assignment.label) payload.label = assignment.label;
        return Webfield2.api.post('/edges?awaitProcess=true', payload);
      });
    });
    return chain;
      }).then(function() {
    setRemoveSelectedReviewersStatus('Removal submitted. Verifying reviewer removal readback...', false);
    setAutoAssignStatus('Removal submitted. Verifying reviewer removal readback...', false);
    return waitForReviewerRemovalReadback(selectedAssignments.map(function(assignment) { return assignment.reviewer; }), {
      onProgress: function(attempt, maxAttempts) {
        var message = 'Removal submitted. Verifying reviewer removal readback... attempt ' + attempt + '/' + maxAttempts + '.';
        setRemoveSelectedReviewersStatus(message, false);
        setAutoAssignStatus(message, false);
      }
    });
      }).then(function() {
    button.prop('disabled', false).text('Remove selected reviewers');
    $('.remove-assigned-reviewer').prop('checked', false);
    setRemoveSelectedReviewersStatus('Removed selected reviewer(s). Refresh the page to see current reviewer assignments.', false);
    setAutoAssignStatus('Removed selected reviewer(s). Refresh the page to see current reviewer assignments.', false);
      }, function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to remove selected reviewers.';
    button.prop('disabled', false).text('Remove selected reviewers');
    setRemoveSelectedReviewersStatus(message, true);
    setAutoAssignStatus(message, true);
      });
    }

    function getReviewerAssignmentRequestedMode() {
      if (typeof args !== 'undefined' && args && args.mode) {
    var argMode = String(args.mode || '').toLowerCase();
    if (argMode === 'add-new') return 'invite';
    if (['auto', 'previous', 'search', 'invite'].indexOf(argMode) >= 0) return argMode;
      }
      var pageLocation =
    (typeof globalThis !== 'undefined' && globalThis.location) ||
    (typeof document !== 'undefined' && document && document.location) ||
    (typeof location !== 'undefined' && location);
      var urls = [];
      if (pageLocation && pageLocation.href) urls.push(pageLocation.href);
      if (typeof performance !== 'undefined' && performance.getEntriesByType) {
    (performance.getEntriesByType('navigation') || []).forEach(function(entry) {
      if (entry && entry.name) urls.push(entry.name);
    });
      }
      if (typeof document !== 'undefined' && document && document.referrer) urls.push(document.referrer);
      for (var i = 0; i < urls.length; i += 1) {
    try {
      var baseUrl = pageLocation && pageLocation.origin ? pageLocation.origin : null;
      var url = baseUrl ? new URL(urls[i], baseUrl) : new URL(urls[i]);
      var hashParams = new URLSearchParams(String(url.hash || '').replace(/^#/, ''));
      var mode = String(url.searchParams.get('mode') || hashParams.get('mode') || '').toLowerCase();
      if (mode === 'add-new') return 'invite';
      if (['auto', 'previous', 'search', 'invite'].indexOf(mode) >= 0) return mode;
    } catch (error) {
      // Ignore malformed referrer/navigation values.
    }
      }
      return '';
    }

    function applyReviewerAssignmentRequestedMode() {
      var mode = getReviewerAssignmentRequestedMode();
      var marker = $('#jmlr-reviewer-assignment-mode-applied');
      if (!mode || (marker.length && marker.attr('data-mode') === mode)) return;
      marker.remove();
      if (mode === 'auto') {
    $('body').append('<span id="jmlr-reviewer-assignment-mode-applied" data-mode="auto" style="display:none;"></span>');
    $('#auto-assign-reviewers').trigger('click');
      } else if (mode === 'search') {
    $('body').append('<span id="jmlr-reviewer-assignment-mode-applied" data-mode="search" style="display:none;"></span>');
    $('#search-reviewers').trigger('click');
      } else if (mode === 'previous' && hasPreviousSubmissionReference()) {
    $('body').append('<span id="jmlr-reviewer-assignment-mode-applied" data-mode="previous" style="display:none;"></span>');
    $('#previous-reviewers').trigger('click');
      } else if (mode === 'invite') {
    $('body').append('<span id="jmlr-reviewer-assignment-mode-applied" data-mode="invite" style="display:none;"></span>');
    $('#invite-new-reviewer').trigger('click');
      }
    }

    function reviewerEligibilityStatus(candidate) {
      candidate = candidate || {};
      candidate.blockers = [];
      if (candidate.cooldownBlocked) candidate.blockers.push({ code: 'cooldown', label: 'Cooldown until ' + formatAutoAssignDate(candidate.cooldownUntil) });
      candidate.classification = classifyReviewerCandidate(candidate);
      var blockerCodes = reviewerCandidateBlockerCodes(candidate);
      return {
    status: candidate.classification.quickLabel || (candidate.classification.eligible ? 'Looks eligible' : 'Not eligible'),
    statusLabel: reviewerCandidateStatusLabel(candidate),
    severity: candidate.classification.severity || 'blocked',
    blockerCodes: blockerCodes,
    overrideAllowed: reviewerCandidateOverrideAllowed(candidate),
    enabled: !!candidate.classification.eligible,
    classification: candidate.classification
      };
    }
"""
