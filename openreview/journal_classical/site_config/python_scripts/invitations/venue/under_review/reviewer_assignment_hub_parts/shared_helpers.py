REVIEWER_ASSIGNMENT_SHARED_JS = r"""    function getEdgeWeight(edge, fallback) {
      var weight = edge && edge.weight;
      return weight === undefined || weight === null ? fallback : Number(weight);
    }

    function reviewerAssignmentBrowserContract() {
      return AUTO_ASSIGN_CONFIG.assignmentBrowserContract || {};
    }

    function reviewerAssignmentInvitationId() {
      return reviewerAssignmentBrowserContract().assignment_invitation || AUTO_ASSIGN_CONFIG.reviewersAssignmentId;
    }

    function extractOnDemandReviewerAffinityScore(results, noteId, tail) {
      var rows = [];
      var collectRows = function(value) {
    if (!value) return;
    if (Array.isArray(value)) {
      value.forEach(collectRows);
      return;
    }
    if (typeof value === 'object') {
      rows.push(value);
      Object.keys(value).forEach(function(key) {
        if (key !== 'publication' && key !== 'profile') collectRows(value[key]);
      });
    }
      };
      collectRows(results);
      for (var index = 0; index < rows.length; index += 1) {
    var row = rows[index] || {};
    var rowNoteId = row.submission || row.submission_id || row.submissionId || row.paper || row.paper_id || row.paperId || row.forum || row.note || row.note_id || row.noteId || row.head || row.entityB || row.id;
    if (rowNoteId && typeof rowNoteId === 'object') rowNoteId = rowNoteId.id || rowNoteId.forum || rowNoteId.noteId;
    if (rowNoteId === noteId) {
      var scoreMap = row.scores || row.scoreByUser || row.userScores || row.members || row.users;
      if (scoreMap && scoreMap[tail] !== undefined && !isNaN(Number(scoreMap[tail]))) return Number(scoreMap[tail]);
    }
    var rowTail = row.user || row.user_id || row.userId || row.profile || row.profile_id || row.profileId || row.member || row.member_id || row.memberId || row.tail || row.entityA;
    if (rowTail && typeof rowTail === 'object') rowTail = rowTail.id || rowTail.profile_id || rowTail.user;
    var score = row.score || row.weight || row.value || row.similarity;
    if (rowNoteId === noteId && rowTail === tail && score !== undefined && !isNaN(Number(score))) return Number(score);
      }
      return null;
    }

    function requestOnDemandReviewerAffinity(tail) {
      if (!tail || tail.charAt(0) !== '~') {
    return $.Deferred().resolve({ tail: tail, score: null, missing: true }).promise();
      }
      var jobName = [
    'jmlr',
    AUTO_ASSIGN_CONFIG.venueId.replace(/\//g, '-'),
    'reviewer-affinity',
    'paper' + AUTO_ASSIGN_CONFIG.paperNumber,
    tail.replace(/[^A-Za-z0-9_~.-]/g, ''),
    Date.now()
      ].join('-');
      var payload = {
    name: jobName,
    entityA: {
      type: 'Group',
      reviewerIds: [tail]
    },
    entityB: {
      type: 'Note',
      submissions: [{
        id: AUTO_ASSIGN_CONFIG.noteId,
        title: AUTO_ASSIGN_CONFIG.submissionTitle || '',
        abstract: AUTO_ASSIGN_CONFIG.submissionAbstract || ''
      }]
    },
    model: {
      name: AUTO_ASSIGN_CONFIG.expertiseModel || 'specter2+scincl',
      normalizeScores: false
    }
      };
      return Webfield2.api.post('/expertise', payload).then(function(response) {
    var jobId = response && (response.jobId || response.job_id || response.id);
    if (!jobId) return { tail: tail, score: null, missing: true };
    return Webfield2.api.get('/expertise/status', { jobId: jobId }).then(function(statusResponse) {
      if (statusResponse && statusResponse.status && statusResponse.status !== 'Completed') {
        return { tail: tail, score: null, missing: true, jobId: jobId, status: statusResponse.status };
      }
      return Webfield2.api.get('/expertise/results', { jobId: jobId }).then(function(results) {
        var score = extractOnDemandReviewerAffinityScore(results, AUTO_ASSIGN_CONFIG.noteId, tail);
        if (score === null) return { tail: tail, score: null, missing: true, jobId: jobId };
        return Webfield2.api.getAll('/edges', {
          invitation: AUTO_ASSIGN_CONFIG.reviewersAffinityScoreId,
          head: AUTO_ASSIGN_CONFIG.noteId,
          tail: tail,
          domain: AUTO_ASSIGN_CONFIG.venueId
        }).then(function(existingEdges) {
          var activeEdge = (existingEdges || []).filter(function(edge) { return edge && !edge.ddate; })[0] || null;
          var edgePayload = {
            invitation: AUTO_ASSIGN_CONFIG.reviewersAffinityScoreId,
            signatures: [AUTO_ASSIGN_CONFIG.venueId],
            head: AUTO_ASSIGN_CONFIG.noteId,
            tail: tail,
            weight: score
          };
          if (activeEdge && activeEdge.id) edgePayload.id = activeEdge.id;
          return Webfield2.api.post('/edges', edgePayload).then(function() {
            return { tail: tail, score: score, missing: false, jobId: jobId };
          }, function() {
            return { tail: tail, score: score, missing: false, jobId: jobId };
          });
        });
      });
    });
      }, function() {
    return { tail: tail, score: null, missing: true };
      });
    }

    function materializeOnDemandReviewerConflict(tail, actorSignature) {
      if (!tail || !actorSignature) {
    return $.Deferred().reject({ message: 'Missing reviewer conflict refresh inputs.' }).promise();
      }
      return withAutoAssignTimeout(Webfield2.api.post('/notes/edits?awaitProcess=true', {
    invitation: AUTO_ASSIGN_CONFIG.venueId + '/-/Assignment_Candidate_Conflict_Refresh',
    signatures: [actorSignature],
    note: {
      content: {
        note_id: { value: AUTO_ASSIGN_CONFIG.noteId },
        paper_number: { value: AUTO_ASSIGN_CONFIG.paperNumber },
        candidate_id: { value: tail },
        role: { value: 'reviewer' }
      }
    }
      }), 45000, 'Timed out refreshing reviewer conflict status. Try again or reload the assignment page.');
    }

    function formatAutoAssignDate(timestamp) {
      if (!timestamp) return '';
      return new Date(timestamp).toISOString().slice(0, 10);
    }

    function getReviewerCooldownStatus(assignmentEdges) {
      var cooldownEdges = (assignmentEdges || []).filter(function(edge) {
    return !AUTO_ASSIGN_CONFIG.previousSubmissionId || edge.head !== AUTO_ASSIGN_CONFIG.previousSubmissionId;
      });
      var until = typeof JMLRPermissionHelpers !== 'undefined' && JMLRPermissionHelpers.getAssignmentCooldownUntil
    ? JMLRPermissionHelpers.getAssignmentCooldownUntil(cooldownEdges, AUTO_ASSIGN_CONFIG.noteId, AUTO_ASSIGN_CONFIG.reviewerNewAssignmentCooldownDays, Date.now())
    : null;
      if (!until) {
    var cooldownMillis = Number(AUTO_ASSIGN_CONFIG.reviewerNewAssignmentCooldownDays || 0) * 24 * 60 * 60 * 1000;
    var now = Date.now();
    var cutoff = now - cooldownMillis;
    var latestRecentAssignment = (cooldownEdges || []).filter(function(edge) {
      return edge && !edge.ddate && edge.head !== AUTO_ASSIGN_CONFIG.noteId && edge.cdate && edge.cdate >= cutoff;
    }).sort(function(a, b) {
      return Number(b.cdate || 0) - Number(a.cdate || 0);
    })[0] || null;
    until = latestRecentAssignment ? latestRecentAssignment.cdate + cooldownMillis : null;
      }
      if (!until) return { blocked: false, until: 0 };
      var sourceEdge = cooldownEdges.filter(function(edge) {
    return edge && !edge.ddate && edge.cdate && edge.cdate + AUTO_ASSIGN_CONFIG.reviewerNewAssignmentCooldownDays * 24 * 60 * 60 * 1000 === until;
      })[0] || null;
      return {
    blocked: true,
    until: until,
    head: sourceEdge && sourceEdge.head
      };
    }

    function isAssignmentAvailable(edge) {
      if (!edge || edge.label !== 'Unavailable') return true;
      return edge.weight && Number(edge.weight) <= Date.now();
    }

    function escapeAutoAssignHtml(value) {
      return String(value === undefined || value === null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
    }

    function reviewerContinuityRowForTail(tail) {
      var continuity = AUTO_ASSIGN_CONFIG.reviewerIdentityContinuity || {};
      var rows = continuity.reviewers || [];
      for (var i = 0; i < rows.length; i += 1) {
    if (rows[i] && rows[i].reviewer_profile_id === tail) return rows[i];
      }
      return null;
    }

    function reviewerContinuityLabelForTail(tail, fallbackLabel) {
      var row = reviewerContinuityRowForTail(tail);
      if (!row) return fallbackLabel || tail;
      var stableNumber = row.stable_number || String(row.stable_label || '').replace(/[^0-9]/g, '');
      var anonId = row.current_anon_id || row.previous_anon_id || '';
      if (anonId && stableNumber) return 'Reviewer ' + anonId + ' (Reviewer ' + stableNumber + ')';
      if (stableNumber) return 'Reviewer ' + stableNumber;
      return fallbackLabel || tail;
    }

    function getReviewerAssignmentSubmission() {
      return {
    id: AUTO_ASSIGN_CONFIG.noteId,
    number: AUTO_ASSIGN_CONFIG.paperNumber,
    content: {
      authorids: AUTO_ASSIGN_CONFIG.submissionAuthorIds || [],
      author_list: AUTO_ASSIGN_CONFIG.submissionAuthorList || '',
      conflict_of_interests: AUTO_ASSIGN_CONFIG.submissionConflictOfInterests || ''
    }
      };
    }

    function reviewerAssignmentConfigList(value) {
      if (Array.isArray(value)) return value;
      if (value === undefined || value === null || value === '') return [];
      return [value];
    }

    function reviewerAssignmentConfigProfileIds(value) {
      var ids = [];
      reviewerAssignmentConfigList(value).forEach(function(item) {
    String(item || '').split(/[\s,;|()[\]<>]+/).forEach(function(token) {
      if (/^~[A-Za-z0-9_]+[0-9]*$/.test(token)) ids.push(token);
    });
      });
      return _.uniq(ids);
    }

    function getReviewerAssignmentHardAuthorConflict(profileId) {
      if (!profileId) return null;
      var authorProfileIds = _.uniq(
    reviewerAssignmentConfigList(AUTO_ASSIGN_CONFIG.submissionAuthorIds || [])
      .concat(reviewerAssignmentConfigProfileIds(AUTO_ASSIGN_CONFIG.submissionAuthorList || ''))
      );
      var declaredConflictProfileIds = reviewerAssignmentConfigProfileIds(AUTO_ASSIGN_CONFIG.submissionConflictOfInterests || '');
      if (authorProfileIds.indexOf(profileId) >= 0) {
    return {
      severity: 'error',
      reason: 'author_list',
      label: 'Author conflict: paper author'
    };
      }
      if (declaredConflictProfileIds.indexOf(profileId) >= 0) {
    return {
      severity: 'error',
      reason: 'conflict_list',
      label: 'Author conflict: author-declared conflict list'
    };
      }
      return null;
    }

    function getReviewerAvailabilityState(edge) {
      if (typeof JMLRPermissionHelpers !== 'undefined' && JMLRPermissionHelpers.getAssignmentAvailabilityState) {
    return JMLRPermissionHelpers.getAssignmentAvailabilityState(edge, Date.now());
      }
      if (!edge || edge.label !== 'Unavailable') return { state: 'available', label: 'Available' };
      var weight = Number(edge.weight || 0);
      if (weight && weight <= Date.now()) return { state: 'available', label: 'Available' };
      if (weight) return { state: 'until', label: 'Unavailable until ' + formatAutoAssignDate(weight), until: weight };
      return { state: 'indefinite', label: 'Unavailable indefinitely' };
    }

    function getPaperScopedReviewerAvailability(tail) {
      var availability = AUTO_ASSIGN_CONFIG.reviewerAssignmentAvailability || {};
      if (availability[tail] && availability[tail].unavailableForAssignment) {
    return { state: 'unavailable', label: 'Unavailable for assignment' };
      }
      return { state: 'available', label: 'Available' };
    }

    function reviewerCandidateInput(candidate) {
      candidate = candidate || {};
      return {
    id: candidate.tail,
    tail: candidate.tail,
    name: candidate.name || candidate.tail,
    email: candidate.email || '',
    institution: candidate.affiliation || '',
    conflictEdge: candidate.conflictEdge || null,
    availability: candidate.availability || null,
    availabilityEdge: candidate.availabilityEdge || null,
    activePaperLoad: candidate.activePaperLoad,
    maxPapers: candidate.maxPapers,
    cooldown_until: candidate.cooldownUntil,
    assigned: candidate.assigned,
    current: candidate.assigned,
    active: candidate.active !== false,
    blockers: candidate.blockers || []
      };
    }

    function classifyReviewerCandidate(candidate) {
      if (typeof JMLRPermissionHelpers !== 'undefined' && JMLRPermissionHelpers.classifyAssignmentCandidate) {
    return JMLRPermissionHelpers.classifyAssignmentCandidate(
      getReviewerAssignmentSubmission(),
      reviewerCandidateInput(candidate),
      { role: 'reviewer' }
    );
      }
      var blockers = [];
      if (candidate.assigned) blockers.push({ code: 'current_assignment', label: 'Current assignment' });
      if (candidate.active === false) blockers.push({ code: 'not_reviewer_member', label: 'Not an active JMLR reviewer' });
      if (candidate.cooldownBlocked) blockers.push({ code: 'cooldown', label: 'Cooldown until ' + formatAutoAssignDate(candidate.cooldownUntil) });
      if (candidate.activePaperLoad >= candidate.maxPapers) blockers.push({ code: 'at_max_load', label: 'At max load' });
      var openreviewConflict = Number(candidate.conflictWeight || 0) !== 0;
      var unavailable = !candidate.availabilityAvailable;
      var eligible = !openreviewConflict && !unavailable && !blockers.length;
      var severity = eligible ? 'eligible' : (unavailable ? 'unavailable' : (blockers.length ? 'blocked' : (openreviewConflict ? 'warning_conflict' : 'blocked')));
      return {
    eligible: eligible,
    severity: severity,
    quickLabel: eligible ? 'Looks eligible' : (unavailable ? 'Unavailable' : (blockers[0] && blockers[0].label || (openreviewConflict ? 'OpenReview conflict' : 'Not eligible'))),
    conflict: {
      hasConflict: openreviewConflict,
      kind: openreviewConflict ? 'openreview_positive' : 'none_detected',
      label: openreviewConflict ? 'OpenReview conflict' : 'None detected',
      selectable: !unavailable && !blockers.length,
      overridable: openreviewConflict && !unavailable && !blockers.length,
      reasons: openreviewConflict ? [{ code: 'openreview_positive', label: 'OpenReview conflict' }] : []
    },
    availability: getReviewerAvailabilityState(candidate.availabilityEdge),
    blockers: blockers,
    detailLabels: []
      };
    }

    function reviewerCandidateBlockerCodes(candidate) {
      var classification = candidate && candidate.classification || {};
      var codes = [];
      if (classification.conflict && classification.conflict.kind === 'author_conflict') codes.push('hard_conflict');
      if (classification.conflict && classification.conflict.kind === 'openreview_positive') codes.push('openreview_conflict');
      if (classification.availability && classification.availability.state && classification.availability.state !== 'available') codes.push('availability');
      (classification.blockers || []).forEach(function(blocker) {
    if (blocker && blocker.code) codes.push(blocker.code);
      });
      if (candidate && candidate.active === false && codes.indexOf('inactive') < 0) codes.push('inactive');
      return _.uniq(codes);
    }

    function reviewerCandidateStatusLabel(candidate) {
      candidate = candidate || {};
      var classification = candidate.classification || {};
      if (classification.severity === 'eligible') return 'Eligible';
      if (classification.severity === 'warning_conflict') return 'OpenReview conflict warning';
      if (classification.conflict && classification.conflict.kind === 'author_conflict') return classification.conflict.label || 'Hard conflict';
      if (classification.availability && classification.availability.state !== 'available') return classification.availability.label || 'Unavailable';
      if (classification.blockers && classification.blockers.length) {
    return classification.blockers.map(function(blocker) { return blocker.label; }).join('; ');
      }
      return classification.quickLabel || 'Not eligible';
    }

    function reviewerCandidateOverrideAllowed(candidate) {
      var classification = candidate && candidate.classification || {};
      return classification.severity === 'warning_conflict' &&
    (!classification.conflict || classification.conflict.overridable !== false) &&
    reviewerCandidateBlockerCodes(candidate).filter(function(code) {
      return code !== 'openreview_conflict';
    }).length === 0;
    }

    function reviewerCandidateEffectivelySelectable(candidate, overrideChecked) {
      candidate = candidate || {};
      if (candidate.eligibility && candidate.eligibility.enabled) return true;
      return !!(overrideChecked && reviewerCandidateOverrideAllowed(candidate));
    }

    function reviewerCandidateRowAttributes(candidate, overrideChecked) {
      candidate = candidate || {};
      var classification = candidate.classification || {};
      var blockerCodes = reviewerCandidateBlockerCodes(candidate);
      var overrideAllowed = reviewerCandidateOverrideAllowed(candidate);
      var selectable = reviewerCandidateEffectivelySelectable(candidate, overrideChecked);
      return ' data-reviewer-tail="' + escapeAutoAssignHtml(candidate.tail || '') + '"' +
    ' data-reviewer-eligibility="' + escapeAutoAssignHtml(classification.severity || 'blocked') + '"' +
    ' data-reviewer-status="' + escapeAutoAssignHtml(reviewerCandidateStatusLabel(candidate)) + '"' +
    ' data-reviewer-blockers="' + escapeAutoAssignHtml(blockerCodes.join(',')) + '"' +
    ' data-reviewer-selectable="' + (selectable ? 'true' : 'false') + '"' +
    ' data-reviewer-override-allowed="' + (overrideAllowed ? 'true' : 'false') + '"' +
    ' data-reviewer-hard-conflict="' + (blockerCodes.indexOf('hard_conflict') >= 0 ? 'true' : 'false') + '"' +
    ' data-reviewer-openreview-conflict="' + (blockerCodes.indexOf('openreview_conflict') >= 0 ? 'true' : 'false') + '"';
    }

    function formatReviewerConflictCell(candidate, currentLabel) {
      if (currentLabel) return escapeAutoAssignHtml(currentLabel);
      var classification = candidate.classification || {};
      var conflictReasons = classification.conflict && classification.conflict.reasons || [];
      var labels = [];
      if (classification.availability && classification.availability.state !== 'available') {
    var availabilityLabel = classification.availability.label || 'Unavailable';
    if (labels.indexOf(availabilityLabel) < 0) labels.push(availabilityLabel);
      }
      (classification.blockers || []).forEach(function(blocker) {
    if (blocker && blocker.label && labels.indexOf(blocker.label) < 0) labels.push(blocker.label);
      });
      conflictReasons.forEach(function(reason) {
    if (reason && reason.label && labels.indexOf(reason.label) < 0) labels.push(reason.label);
      });
      if (labels.length) {
    var conflictKind = classification.conflict && classification.conflict.kind;
    var conflictClass = conflictKind === 'author_conflict' ? 'text-danger' : 'text-warning';
    var conflictLabel = classification.conflict && classification.conflict.label || 'Conflict';
    var heading = conflictKind === 'author_conflict' && conflictReasons.length
      ? '<strong class="' + conflictClass + '">' + escapeAutoAssignHtml(conflictLabel) + '</strong><br>'
      : '';
    return heading + '<ul style="padding-left: 16px; margin-bottom: 0;">' +
      labels.map(function(label) { return '<li>' + escapeAutoAssignHtml(label) + '</li>'; }).join('') +
      '</ul>';
      }
      return '<span class="text-muted">None detected</span>';
    }

    function renderReviewerAssignmentHomepageStrip() {
      if (typeof JMLRPermissionHelpers !== 'undefined' && JMLRPermissionHelpers.renderVenueHomepageStrip) {
    JMLRPermissionHelpers.renderVenueHomepageStrip({
      container: '#invitation-container',
      venueId: AUTO_ASSIGN_CONFIG.venueId,
      $: $
    });
    return;
      }
      if ($('#jmlr-venue-homepage-strip-style').length === 0) {
    $('head').append(
      '<style id="jmlr-venue-homepage-strip-style">' +
        '#edit-banner { display: none !important; }' +
        '#jmlr-venue-homepage-strip-container { margin: 0; padding: 0; }' +
        '#jmlr-venue-homepage-strip { background: #f2dede; border: 0; border-top: 1px solid #ebccd1; border-bottom: 1px solid #ebccd1; box-sizing: border-box; color: #a94442; margin: 0; padding: 8px 15px; position: relative; width: 100%; }' +
        '#jmlr-venue-homepage-strip a { color: #8a1f11; font-weight: 600; }' +
      '</style>'
    );
      }
      $('#jmlr-venue-homepage-strip-container').remove();
      $('#invitation-container').prepend(
    '<div id="jmlr-venue-homepage-strip-container">' +
      '<div id="jmlr-venue-homepage-strip">' +
        '<a href="/group?id=' + encodeURIComponent(AUTO_ASSIGN_CONFIG.venueId) + '">Go to JMLR homepage</a>' +
      '</div>' +
    '</div>'
      );
      function getReviewerAssignmentBootstrapContentInset(viewportWidth) {
    if (viewportWidth >= 1200) return Math.round((viewportWidth - 1170) / 2 + 15);
    if (viewportWidth >= 992) return Math.round((viewportWidth - 970) / 2 + 15);
    if (viewportWidth >= 768) return Math.round((viewportWidth - 750) / 2 + 15);
    return 15;
      }
      function syncReviewerAssignmentHomepageStripLayout() {
    var stripContainer = $('#jmlr-venue-homepage-strip-container');
    var strip = $('#jmlr-venue-homepage-strip');
    var nav = $('nav').first();
    if (!stripContainer.length || !strip.length || !nav.length) return;
    if (!strip[0].getBoundingClientRect || !nav[0].getBoundingClientRect) return;
    var documentElement = typeof document !== 'undefined' && document && document.documentElement;
    var navRect = nav[0].getBoundingClientRect();
    var viewportWidth = navRect && navRect.width
      ? Math.round(navRect.width)
      : (documentElement && documentElement.clientWidth
        ? documentElement.clientWidth
      : (typeof globalThis !== 'undefined' && globalThis.innerWidth ? globalThis.innerWidth : stripContainer[0].getBoundingClientRect().width)
      );
    var parentRect = stripContainer.parent().length && stripContainer.parent()[0].getBoundingClientRect
      ? stripContainer.parent()[0].getBoundingClientRect()
      : { left: 0 };
    var contentInset = getReviewerAssignmentBootstrapContentInset(viewportWidth);
    strip.css({
      left: Math.round((navRect && navRect.left ? navRect.left : 0) - parentRect.left) + 'px',
      width: Math.round(viewportWidth) + 'px',
      'padding-left': contentInset + 'px',
      'padding-right': contentInset + 'px'
    });
    stripContainer.css('margin-top', '0px');
    var gap = Math.round(strip[0].getBoundingClientRect().top - navRect.bottom);
    stripContainer.css('margin-top', gap > 0 ? (-gap) + 'px' : '0px');
      }
      syncReviewerAssignmentHomepageStripLayout();
      var eventTarget = typeof globalThis !== 'undefined'
    ? globalThis
    : (typeof window !== 'undefined' ? window : null);
      if (eventTarget && eventTarget.addEventListener) {
    eventTarget.addEventListener('resize', syncReviewerAssignmentHomepageStripLayout);
      }
    }

    function setReviewerAssignmentButtonBusy(button) {
      if (!button || !button.length) return;
      if (!button.data('reviewerAssignmentOriginalText')) {
    button.data('reviewerAssignmentOriginalText', button.text());
      }
      button.prop('disabled', true);
    }

    function restoreReviewerAssignmentButton(button) {
      if (!button || !button.length) return;
      var originalText = button.data('reviewerAssignmentOriginalText') || button.text();
      button.prop('disabled', false).text(originalText);
      button.removeData('reviewerAssignmentOriginalText');
    }

    function setReviewerAssignmentButtonStatus(button, message, isError) {
      if (!button || !button.length) return;
      var status = button.siblings('.reviewer-assignment-button-status').first();
      status.text(message || '')
    .toggleClass('text-danger', !!isError)
    .toggleClass('text-success', !isError && !!message)
    .toggleClass('text-muted', !isError);
    }

    function setReviewerAssignmentProgress(button, message, isError) {
      setAutoAssignStatus(message, isError);
      setReviewerAssignmentButtonStatus(button, message, isError);
    }

    function showReviewerAssignmentComplete(button, message) {
      var finalMessage = (message || 'Reviewer assignment complete.').replace(/\s*Refreshing\.\.\.?\s*$/i, '');
      setReviewerAssignmentProgress(button, finalMessage + ' Done. Refresh the page to see current reviewer assignments.', false);
      restoreReviewerAssignmentButton(button);
    }

    function withAutoAssignTimeout(promise, timeoutMillis, timeoutMessage) {
      var deferred = $.Deferred();
      var settled = false;
      var timer = setTimeout(function() {
    if (settled) return;
    settled = true;
    deferred.reject({ message: timeoutMessage || 'Reviewer assignment request timed out.' });
      }, timeoutMillis || 45000);
      $.when(promise).then(function() {
    if (settled) return;
    settled = true;
    clearTimeout(timer);
    deferred.resolve.apply(deferred, arguments);
      }, function() {
    if (settled) return;
    settled = true;
    clearTimeout(timer);
    deferred.reject.apply(deferred, arguments);
      });
      return deferred.promise();
    }

    function emptyReviewerStats() {
      var ratingsMap = {};
      Object.keys(AUTO_ASSIGN_CONFIG.ratingScores || {}).forEach(function(label) { ratingsMap[label] = 0; });
      var timelinessMap = {};
      (AUTO_ASSIGN_CONFIG.timelinessOrder || []).forEach(function(label) { timelinessMap[label] = 0; });
      return { ratingsMap: ratingsMap, timelinessMap: timelinessMap, ratingCount: 0, ratingTotal: 0, averageRating: 0, sourceStatus: 'loaded' };
    }

    function unavailableReviewerStats(reason) {
      var stats = emptyReviewerStats();
      stats.sourceStatus = 'unavailable';
      stats.sourceReason = reason || 'reviewer statistics source unavailable';
      return stats;
    }

    function addReviewerRating(stats, ratingNote) {
      stats = stats || emptyReviewerStats();
      var content = ratingNote && ratingNote.content || {};
      var rating = content.rating && content.rating.value || 'No rating';
      if (stats.ratingsMap[rating] === undefined) stats.ratingsMap[rating] = 0;
      stats.ratingsMap[rating] += 1;
      stats.ratingCount += 1;
      stats.ratingTotal += Number((AUTO_ASSIGN_CONFIG.ratingScores || {})[rating] || 0);
      stats.averageRating = stats.ratingCount ? stats.ratingTotal / stats.ratingCount : 0;
      var timeliness = content.timeliness && content.timeliness.value;
      if (timeliness) {
    if (stats.timelinessMap[timeliness] === undefined) stats.timelinessMap[timeliness] = 0;
    stats.timelinessMap[timeliness] += 1;
      }
      stats.sourceStatus = 'loaded';
      return stats;
    }

    function reviewerRatingHelpText() {
      return Object.keys(AUTO_ASSIGN_CONFIG.ratingScores || {}).map(function(label) {
    var score = Number(AUTO_ASSIGN_CONFIG.ratingScores[label] || 0);
    return label + ' = ' + (score > 0 ? '+' : '') + score;
      }).join('; ');
    }

    function reviewerStatsSummary(stats) {
      if (!stats) return 'Rating/timeliness history unavailable';
      if (stats.sourceStatus === 'unavailable') return 'Rating/timeliness history unavailable';
      if (!stats.ratingCount) return 'No rating history';
      var timeliness = (AUTO_ASSIGN_CONFIG.timelinessOrder || []).map(function(label) {
    return stats.timelinessMap && stats.timelinessMap[label] || 0;
      }).join(' / ');
      return 'Rating ' + stats.averageRating.toFixed(2) + ' (' + stats.ratingCount + '); Timeliness ' + timeliness;
    }

    function getReviewerProfileIdFromRating(note) {
      var content = note && note.content || {};
      return content.reviewer_profile_id && content.reviewer_profile_id.value || null;
    }

    function noteIsReviewerRating(note) {
      return (note && note.invitations || []).some(function(invitation) {
    return /\/Reviewer_[^/]+\/-\/Rating$/.test(invitation || '');
      });
    }

    function getReviewerStatsByTail(tails) {
      tails = _.uniq((tails || []).filter(function(tail) { return !!tail && tail.charAt(0) === '~'; }));
      var requested = tails.reduce(function(byTail, tail) {
    byTail[tail] = true;
    return byTail;
      }, {});
      var makeEmptyMap = function() {
    return tails.reduce(function(byTail, tail) {
      byTail[tail] = emptyReviewerStats();
      return byTail;
    }, {});
      };
      if (!tails.length) return $.Deferred().resolve({}).promise();
      return Webfield2.api.getAll('/notes', {
    invitation: AUTO_ASSIGN_CONFIG.venueId + '/-/Submission'
      }).then(function() {
    return tails.reduce(function(byTail, tail) {
      byTail[tail] = unavailableReviewerStats('rating history requires source-backed rating-note index');
      return byTail;
    }, {});
      }, function() {
    return tails.reduce(function(byTail, tail) {
      byTail[tail] = unavailableReviewerStats('reviewer statistics source lookup failed');
      return byTail;
    }, {});
      });
    }

    function edgeIsDeleted(edge) {
      return edge && edge.ddate && Number(edge.ddate) <= Date.now();
    }

    function normalizeInviteStatus(edge, assignmentByTail) {
      if (!edge) return '';
      if (edgeIsDeleted(edge)) return 'Expired';
      var label = edge.label || '';
      if (label === 'Invitation Sent') return 'Pending acceptance';
      if (label === 'Accepted' && assignmentByTail && assignmentByTail[edge.tail]) return 'Assigned';
      if (label === 'Accepted') return 'Accepted';
      if (label.indexOf('Declined') === 0) return 'Declined';
      return label || 'Pending acceptance';
    }

    function setAutoAssignStatus(message, isError) {
      $('#auto-assign-status')
    .text(message || '')
    .toggleClass('text-danger', !!isError)
    .toggleClass('text-success', !isError && !!message);
    }

    function requiredReviewerCountControlHtml(activeAssignmentCount) {
      var maxRequired = Number(AUTO_ASSIGN_CONFIG.maxRequiredReviewers || AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments || 5);
      var currentRequired = Number(AUTO_ASSIGN_CONFIG.numberOfReviewers || 0) || 1;
      return '<div class="panel-body" style="border-bottom: 1px solid #ddd;">' +
    '<div class="form-inline">' +
      '<label for="required-reviewers-count" style="margin-right: 8px;">Required reviewers</label>' +
      '<input id="required-reviewers-count" class="form-control input-sm" type="number" min="1" max="' + maxRequired + '" value="' + currentRequired + '" style="width: 80px; margin-right: 8px;">' +
      '<button id="save-required-reviewers-count" class="btn btn-xs btn-primary" type="button">Save</button>' +
      '<span id="current-reviewer-assignment-count" class="text-muted" style="margin-left: 8px;">Current assignments: ' + activeAssignmentCount + '</span>' +
      '<span id="required-reviewers-count-status" style="margin-left: 8px;"></span>' +
    '</div>' +
      '</div>';
    }

    function setRequiredReviewersStatus(message, isError) {
      $('#required-reviewers-count-status')
    .text(message || '')
    .toggleClass('text-danger', !!isError)
    .toggleClass('text-success', !isError && !!message);
    }

    function saveRequiredReviewerCount() {
      var input = $('#required-reviewers-count');
      var button = $('#save-required-reviewers-count');
      var value = Number(input.val());
      var maxRequired = Number(AUTO_ASSIGN_CONFIG.maxRequiredReviewers || AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments || 5);
      if (!value || value < 1 || value > maxRequired || Math.floor(value) !== value) {
    setRequiredReviewersStatus('Enter an integer from 1 to ' + maxRequired + '.', true);
    return;
      }
      var currentRequired = Number(AUTO_ASSIGN_CONFIG.numberOfReviewers || 0);
      if (value === currentRequired) {
    setRequiredReviewersStatus('Already set to ' + value + '.', false);
    return;
      }
      var activeAssignmentCount = Number(input.attr('data-active-assignments') || 0);
      if (value <= activeAssignmentCount && typeof confirm === 'function') {
    var confirmed = confirm('This will set the required reviewer count to ' + value + ', which is at or below the current assigned reviewer count of ' + activeAssignmentCount + '. Continue?');
    if (!confirmed) return;
      }
      button.prop('disabled', true).text('Saving...');
      setRequiredReviewersStatus('Saving required reviewer count...', false);
      getAutoAssignmentSignature().then(function(signature) {
    return Webfield2.api.get('/edges', {
      invitation: AUTO_ASSIGN_CONFIG.requiredReviewersId,
      head: AUTO_ASSIGN_CONFIG.noteId,
      tail: AUTO_ASSIGN_CONFIG.requiredReviewersTail
    }).then(function(response) {
      var edges = response && response.edges || response || [];
      var activeEdge = _.find(edges, function(edge) { return edge && !edge.ddate; });
      var payload = {
      invitation: AUTO_ASSIGN_CONFIG.requiredReviewersId,
      signatures: [signature],
      head: AUTO_ASSIGN_CONFIG.noteId,
      tail: AUTO_ASSIGN_CONFIG.requiredReviewersTail,
      weight: value,
      label: 'Required Reviewers'
      };
      if (activeEdge && activeEdge.id) payload.id = activeEdge.id;
      return Webfield2.api.post('/edges', payload);
    });
      }).then(function() {
    AUTO_ASSIGN_CONFIG.numberOfReviewers = value;
    button.prop('disabled', false).text('Save');
    setRequiredReviewersStatus('Saved. Refresh the page to see current reviewer assignment settings.', false);
    setAutoAssignStatus('Required reviewer count saved. Refresh the page to see current reviewer assignment settings.', false);
      }, function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to save required reviewer count.';
    button.prop('disabled', false).text('Save');
    setRequiredReviewersStatus(message, true);
    setAutoAssignStatus(message, true);
      });
    }

    function reviewerAssignmentOverrideLabel(candidate, actorSignature) {
      if (!reviewerCandidateOverrideAllowed(candidate)) return undefined;
      return actorSignature === AUTO_ASSIGN_CONFIG.venueId + '/Editors_In_Chief'
    ? 'EIC OpenReview Conflict Override'
    : 'AE OpenReview Conflict Override';
    }

    function reviewerAssignmentEdgePayload(tail, actorSignature, edgeLabel) {
      var payload = {
    invitation: reviewerAssignmentInvitationId(),
    signatures: [actorSignature],
    head: AUTO_ASSIGN_CONFIG.noteId,
    tail: tail,
    weight: 1
      };
      if (edgeLabel) payload.label = edgeLabel;
      return payload;
    }

    function defaultReviewerDueDateInputValue() {
      var now = new Date();
      var reviewPeriodDays = Number(AUTO_ASSIGN_CONFIG.reviewPeriodDays || 0);
      var dueDate = new Date(Date.UTC(
    now.getUTCFullYear(),
    now.getUTCMonth(),
    now.getUTCDate() + reviewPeriodDays
      ));
      return dueDate.toISOString().slice(0, 10);
    }

    function reviewerDueDateInputHtml(inputId) {
      inputId = inputId || 'new-reviewer-due-date';
      return '<span class="reviewer-due-date-control" style="display: inline-flex; align-items: center; gap: 6px; margin-right: 8px;">' +
    '<label for="' + escapeAutoAssignHtml(inputId) + '" class="small text-muted" style="margin: 0;">Review due date</label>' +
    '<input id="' + escapeAutoAssignHtml(inputId) + '" type="date" class="form-control input-sm" style="width: 150px;" value="' + escapeAutoAssignHtml(defaultReviewerDueDateInputValue()) + '">' +
      '</span>';
    }

    function reviewerDueDateMillisFromInput(inputId) {
      inputId = inputId || 'new-reviewer-due-date';
      var value = String($('#' + inputId).val() || '').trim();
      if (!value) return null;
      var parsed = value.match(/^([0-9]{4})-([0-9]{2})-([0-9]{2})$/);
      if (!parsed) return NaN;
      return Date.UTC(Number(parsed[1]), Number(parsed[2]) - 1, Number(parsed[3]));
    }

    function reviewerDueDateEdgePayload(tail, actorSignature, dueDateMillis) {
      return {
    invitation: AUTO_ASSIGN_CONFIG.reviewersReviewDueDateId,
    signatures: [actorSignature],
    head: AUTO_ASSIGN_CONFIG.noteId,
    tail: tail,
    weight: dueDateMillis,
    label: 'Review Due Date'
      };
    }

    function postReviewerDueDateEdge(tail, actorSignature, dueDateMillis) {
      if (!dueDateMillis) return $.Deferred().resolve().promise();
      var payload = reviewerDueDateEdgePayload(tail, actorSignature, dueDateMillis);
      return withAutoAssignTimeout(
    Webfield2.api.post('/edges', payload),
    45000,
    'Timed out setting reviewer due date. Reload the assignment page to check whether the due date was set.'
      ).then(null, function(error) {
    error = error || {};
    if (typeof error !== 'object') error = { message: String(error) };
    error.assignmentPayload = payload;
    if (typeof Promise !== 'undefined' && Promise.reject) return Promise.reject(error);
    return $.Deferred().reject(error).promise();
      });
    }

    function reviewerAssignmentErrorMessage(error, fallbackMessage) {
      var message = error && error.responseJSON && (error.responseJSON.message || error.responseJSON.name);
      if (!message && error && error.responseText) {
    try {
      var parsed = JSON.parse(error.responseText);
      message = parsed && (parsed.message || parsed.name || parsed.error);
    } catch (parseError) {
      message = error.responseText;
    }
      }
      message = message || error && error.message || error && error.statusText || fallbackMessage || 'Unable to assign selected reviewers.';
      if (error && error.assignmentPayload) {
    var payload = error.assignmentPayload;
    var summary = [
      'invitation ' + payload.invitation,
      'signature ' + (payload.signatures || []).join(','),
      'tail ' + payload.tail
    ];
    if (payload.label) summary.push('label ' + payload.label);
    message += ' (' + summary.join('; ') + ')';
      } else if (error && error.assignmentPayloads && error.assignmentPayloads.length) {
    var payloadSummaries = error.assignmentPayloads.map(function(payload) {
      var summary = [
        'invitation ' + payload.invitation,
        'signature ' + (payload.signatures || []).join(','),
        'tail ' + payload.tail
      ];
      if (payload.label) summary.push('label ' + payload.label);
      return summary.join('; ');
    });
    message += ' (attempted ' + payloadSummaries.join(' | ') + ')';
      }
      if (error && error.status && message.indexOf('HTTP ' + error.status) < 0) {
    message += ' [HTTP ' + error.status + ']';
      }
      return message;
    }

    function postCheckedReviewerAssignmentEdge(tail, actorSignature, edgeLabel, dueDateMillis) {
      var payload = reviewerAssignmentEdgePayload(tail, actorSignature, edgeLabel);
      return postReviewerDueDateEdge(tail, actorSignature, dueDateMillis).then(function() {
    return withAutoAssignTimeout(
      Webfield2.api.post('/edges', payload),
      45000,
      'Timed out submitting reviewer assignment. Reload the assignment page to check whether the assignment was created.'
    );
      }).then(null, function(error) {
    var rejectionArgs = Array.prototype.slice.call(arguments);
    error = error || {};
    if (typeof error !== 'object') error = { message: String(error) };
    if (!error.responseJSON && rejectionArgs.length > 1) error.responseJSON = rejectionArgs[1] && rejectionArgs[1].responseJSON;
    if (!error.responseText && rejectionArgs.length > 1) error.responseText = rejectionArgs[1] && rejectionArgs[1].responseText;
    if (!error.message && rejectionArgs.length > 2 && rejectionArgs[2]) error.message = String(rejectionArgs[2]);
    error.assignmentPayload = payload;
    if (typeof Promise !== 'undefined' && Promise.reject) return Promise.reject(error);
    return $.Deferred().reject(error).promise();
      });
    }

    function getPaperReviewersGroupId() {
      return AUTO_ASSIGN_CONFIG.venueId + '/Paper' + AUTO_ASSIGN_CONFIG.paperNumber + '/Reviewers';
    }
	"""
