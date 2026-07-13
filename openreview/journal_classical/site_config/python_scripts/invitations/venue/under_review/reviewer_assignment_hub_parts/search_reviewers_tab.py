SEARCH_REVIEWERS_TAB_JS = r"""    function showReviewerSearchPanel() {
      hideReviewerInviteForm();
      hidePreviousReviewersPanel();
      $('#confirm-auto-assign-container').remove();
      $('#manual-reviewer-search-container').show();
      var searchPanel = $('#manual-reviewer-search-container')[0];
      if (searchPanel && searchPanel.scrollIntoView) searchPanel.scrollIntoView({ block: 'start', inline: 'nearest' });
      fitReviewerSearchPanelToViewport();
      $('#manual-reviewer-search-input').focus();
      setAutoAssignStatus('Search existing JMLR reviewers by name, email, or OpenReview id.', false);
    }

    function fitReviewerSearchPanelToViewport() {
      var panel = $('#manual-reviewer-search-container');
      if (!panel.length) return;
      panel.css({
    'position': 'static',
    'top': '',
    'left': '',
    'transform': '',
    'width': '',
    'max-height': '',
    'overflow-y': 'visible',
    'z-index': '',
    'box-shadow': ''
      });
      panel.find('.manual-reviewer-search-table').css({
    'max-height': '720px',
    'overflow-y': 'auto'
      });
    }

    function hideReviewerSearchPanel() {
      $('#manual-reviewer-search-container').hide();
      $('#manual-reviewer-search-input').val('');
      $('#manual-reviewer-search-results').empty();
      setAutoAssignStatus('', false);
    }

    function searchExistingReviewers() {
      var query = ($('#manual-reviewer-search-input').val() || '').trim().toLowerCase();
      if (!query) {
    $('#manual-reviewer-search-results').html('<p class="text-danger">Enter a reviewer name, email, or OpenReview profile id.</p>');
    return;
      }
      $('#manual-reviewer-search-results').html('<p class="text-muted">Searching reviewers...</p>');
      var onDemandReviewerAffinityRequests = {};
      var requestMissingReviewerAffinityForCandidates = function(candidates) {
    (candidates || []).forEach(function(candidate) {
      if (!candidate || candidate.hasAffinity || onDemandReviewerAffinityRequests[candidate.tail]) return;
      if (candidate.classification && candidate.classification.severity === 'unavailable') return;
      onDemandReviewerAffinityRequests[candidate.tail] = true;
      requestOnDemandReviewerAffinity(candidate.tail).then(function(result) {
        if (!result || result.score === null || result.score === undefined) return;
        candidate.affinity = result.score;
        candidate.hasAffinity = true;
        var row = $('.manual-reviewer-candidate-row[data-tail="' + candidate.tail.replace(/"/g, '\\"') + '"]');
        row.find('td').eq(4).text(String(result.score));
      });
    });
      };
      var refreshReviewerSearchCandidateConflict = function(candidate, actorSignature) {
    if (!candidate || !candidate.tail) return $.Deferred().resolve(candidate).promise();
    return materializeOnDemandReviewerConflict(candidate.tail, actorSignature).then(function() {
      return getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersConflictId, AUTO_ASSIGN_CONFIG.noteId, [candidate.tail]);
    }, function() {
      return getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersConflictId, AUTO_ASSIGN_CONFIG.noteId, [candidate.tail]);
    }).then(function(conflictsByTail) {
      var conflictEdge = (conflictsByTail[candidate.tail] || [])[0] || null;
      candidate.conflictEdge = conflictEdge;
      candidate.conflictWeight = getEdgeWeight(conflictEdge, 0);
      candidate.eligibility = reviewerEligibilityStatus(candidate);
      return candidate;
    }, function() {
      return candidate;
    });
      };
      var getAllJmlrReviewerTails = function() {
    var configuredReviewerTails = _.uniq((AUTO_ASSIGN_CONFIG.reviewerCandidateTails || []).filter(function(member) {
      return !!member && member.charAt(0) === '~';
    }));
    if (configuredReviewerTails.length) return $.Deferred().resolve(configuredReviewerTails).promise();
    return Webfield2.api.getGroup(AUTO_ASSIGN_CONFIG.reviewersId, { select: 'id,members' }).then(function(group) {
      return _.uniq((group && group.members || []).filter(function(member) {
        return !!member;
      }));
    });
      };
      $.when(
    getAutoAssignmentSignature(),
    getAllJmlrReviewerTails(),
    Webfield2.api.getAll('/edges', { invitation: reviewerAssignmentInvitationId(), head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId, trash: true, stream: true }),
    Webfield2.api.getAll('/edges', { invitation: AUTO_ASSIGN_CONFIG.reviewersAffinityScoreId, head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId })
      ).then(function(signature, reviewerIds, assignmentEdges, affinityEdges) {
    reviewerIds = reviewerIds || [];
    assignmentEdges = assignmentEdges || [];
    affinityEdges = affinityEdges || [];
    var assignedByTail = assignmentEdges.reduce(function(byTail, edge) {
      if (!edge.ddate && edge.tail) byTail[edge.tail] = edge;
      return byTail;
    }, {});
    var affinityByTail = affinityEdges.reduce(function(byTail, edge) {
      byTail[edge.tail] = Math.max(byTail[edge.tail] === undefined ? -Infinity : byTail[edge.tail], getEdgeWeight(edge, -Infinity));
      return byTail;
    }, {});
    getProfilesById(reviewerIds).then(function(profilesById) {
      var matchedReviewerIds = reviewerIds.filter(function(id) {
        var profile = profilesById[id] || null;
        var haystack = [
          id,
          getProfileName(profile, id),
          getProfileSearchEmails(profile, id),
          getProfileAffiliation(profile)
        ].join(' ').toLowerCase();
        return haystack.indexOf(query) >= 0;
      }).sort(function(a, b) {
        var affinityA = affinityByTail[a] === undefined ? -Infinity : affinityByTail[a];
        var affinityB = affinityByTail[b] === undefined ? -Infinity : affinityByTail[b];
        if (affinityB !== affinityA) return affinityB - affinityA;
        return String(a).localeCompare(String(b));
      });
      var displayedMatchLimit = 20;
      var matchedIds = matchedReviewerIds.slice(0, displayedMatchLimit);
      if (!matchedIds.length) {
        $('#manual-reviewer-search-results').html('<p class="text-muted">No existing JMLR reviewer matched this search. Use Invite New Reviewer for external email invitations.</p>');
        return;
      }
      $.when(
        getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersConflictId, AUTO_ASSIGN_CONFIG.noteId, matchedIds),
        getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersPendingReviewsId, null, matchedIds),
        getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersCustomMaxPapersId, null, matchedIds),
        getEdgesByTail(reviewerAssignmentInvitationId(), null, matchedIds)
      ).then(function(conflictsByTail, pendingByTail, maxPapersByTail, assignmentHistoryByTail) {
        getReviewerStatsByTail(matchedIds).then(function(statsByTail) {
        var activeAssignedCount = Object.keys(assignedByTail).length;
        var remainingAssignmentSlots = Math.max(0, AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments - activeAssignedCount);
        var candidates = matchedIds.map(function(tail) {
          var profile = profilesById[tail] || null;
          var cooldownStatus = getReviewerCooldownStatus(assignmentHistoryByTail[tail] || []);
          var availability = getPaperScopedReviewerAvailability(tail);
          var candidate = {
            tail: tail,
            name: getProfileName(profile, tail),
            email: getProfileEmails(profile, tail),
            affiliation: getProfileAffiliation(profile),
            assigned: !!assignedByTail[tail],
            affinity: affinityByTail[tail] === undefined ? 0 : affinityByTail[tail],
            hasAffinity: affinityByTail[tail] !== undefined,
            conflictWeight: getEdgeWeight((conflictsByTail[tail] || [])[0], 0),
            conflictEdge: (conflictsByTail[tail] || [])[0] || null,
            availability: availability,
            availabilityAvailable: availability.state === 'available',
            cooldownBlocked: cooldownStatus.blocked,
            cooldownUntil: cooldownStatus.until,
            activePaperLoad: getEdgeWeight((pendingByTail[tail] || [])[0], 0),
            maxPapers: getEdgeWeight((maxPapersByTail[tail] || [])[0], AUTO_ASSIGN_CONFIG.reviewersMaxPapers),
            active: true,
            ratingStats: statsByTail[tail] || unavailableReviewerStats('reviewer statistics missing from lookup result')
          };
          var eligibility = reviewerEligibilityStatus(candidate);
          candidate.eligibility = eligibility;
          return candidate;
        });
        var conflictOverrideChecked = $('#allow-reviewer-search-conflict-override').prop('checked');
        var hasOpenReviewConflictRows = candidates.some(function(candidate) {
          return reviewerCandidateOverrideAllowed(candidate);
        });
        requestMissingReviewerAffinityForCandidates(candidates);
        var rows = candidates.map(function(candidate) {
          var title = candidate.name === candidate.tail ? candidate.tail : candidate.name + ' (' + candidate.tail + ')';
          var eligibility = candidate.eligibility;
          var isOpenReviewConflict = candidate.classification && candidate.classification.severity === 'warning_conflict';
          var isAuthorConflict = candidate.classification && candidate.classification.severity === 'author_conflict';
          var isUnavailable = candidate.classification && candidate.classification.severity === 'unavailable';
          var selectable = reviewerCandidateEffectivelySelectable(candidate, conflictOverrideChecked);
          var disabled = !selectable || remainingAssignmentSlots <= 0 ? ' disabled' : '';
          var rowClass = 'manual-reviewer-candidate-row';
          if (!selectable) rowClass += ' text-muted';
          if (isOpenReviewConflict) rowClass += ' warning';
          if (isAuthorConflict) rowClass += ' danger';
          var rowStyle = selectable ? 'cursor: pointer;' : (isUnavailable ? 'color: #777; background: #f7f7f7;' : '');
          var reviewerProfileUrl = '/profile?id=' + encodeURIComponent(candidate.tail);
          var reviewerDisplayName = candidate.name || candidate.tail;
          return '<tr class="' + rowClass + '" data-tail="' + escapeAutoAssignHtml(candidate.tail) + '"' + reviewerCandidateRowAttributes(candidate, conflictOverrideChecked) + (rowStyle ? ' style="' + rowStyle + '"' : '') + '>' +
            '<td style="width: 44px; min-width: 44px; max-width: 44px; text-align: center;"><input type="checkbox" class="manual-reviewer-candidate" value="' + escapeAutoAssignHtml(candidate.tail) + '"' + disabled + '></td>' +
            '<td style="width: 260px; min-width: 260px; max-width: 260px; white-space: normal; overflow-wrap: anywhere; word-break: break-word;"><strong><a href="' + reviewerProfileUrl + '" target="_blank" rel="noopener noreferrer" title="' + escapeAutoAssignHtml(title) + '">' + escapeAutoAssignHtml(reviewerDisplayName) + '</a></strong></td>' +
            '<td>' + escapeAutoAssignHtml(candidate.affiliation || '') + '</td>' +
            '<td>' + escapeAutoAssignHtml(reviewerStatsSummary(candidate.ratingStats)) + '</td>' +
            '<td>' + escapeAutoAssignHtml(candidate.hasAffinity ? candidate.affinity : '0 (missing)') + '</td>' +
            '<td>' + escapeAutoAssignHtml(candidate.activePaperLoad) + ' / ' + escapeAutoAssignHtml(candidate.maxPapers) + '</td>' +
            '<td>' + formatReviewerConflictCell(candidate) + '</td>' +
            '</tr>';
        }).join('');
        var matchSummary = matchedReviewerIds.length > displayedMatchLimit
          ? 'Showing the top ' + displayedMatchLimit + ' of ' + matchedReviewerIds.length + ' matching JMLR reviewers. Narrow your search to see more.'
          : 'Showing ' + matchedReviewerIds.length + ' matching JMLR reviewer(s).';
        $('#manual-reviewer-search-results').html(
          '<p class="text-muted">' + escapeAutoAssignHtml(matchSummary) + ' Select existing reviewers from the search results, then confirm the assignment. Current assigned reviewers plus selected reviewers cannot exceed ' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + '.</p>' +
          (hasOpenReviewConflictRows ? '<div class="checkbox"><label><input id="allow-reviewer-search-conflict-override" type="checkbox"' + (conflictOverrideChecked ? ' checked' : '') + '> Allow AE/EIC override for selected OpenReview conflict rows.</label></div>' : '') +
          '<div class="table-responsive manual-reviewer-search-table" style="max-height: 720px; overflow-y: auto; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd;">' +
            '<table class="table table-condensed" style="margin-bottom: 0;">' +
              '<thead><tr><th style="width: 44px; min-width: 44px; max-width: 44px;">Select</th><th style="width: 260px; min-width: 260px; max-width: 260px;">Reviewer</th><th>Affiliation</th><th>Rating / Timeliness</th><th>Affinity</th><th>Load</th><th>Conflicts</th></tr></thead>' +
              '<tbody>' + rows + '</tbody>' +
            '</table>' +
          '</div>' +
          '<p id="manual-reviewer-selection-status" class="small text-muted" style="margin-top: 8px;"></p>' +
          '<p style="position: sticky; bottom: 0; z-index: 2; margin: 10px -15px -15px; padding: 10px 15px; background: #fff; border-top: 1px solid #ddd;">' +
            reviewerDueDateInputHtml() +
            '<button id="assign-selected-search-reviewers" type="button" class="btn btn-primary" disabled>Assign Selected Reviewers</button>' +
            '<span class="reviewer-assignment-button-status text-muted" style="margin-left: 8px;"></span>' +
          '</p>'
        );
        fitReviewerSearchPanelToViewport();
        var updateManualReviewerSelectionState = function() {
          var selectedCount = $('.manual-reviewer-candidate:checked:not(:disabled)').length;
          var totalCount = activeAssignedCount + selectedCount;
          if (totalCount >= AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments) {
            $('.manual-reviewer-candidate:not(:checked):not(:disabled)').prop('disabled', true);
          } else {
            $('.manual-reviewer-candidate').each(function() {
              var tail = $(this).val();
              var candidate = candidates.filter(function(item) { return item.tail === tail; })[0];
              var conflictOverrideChecked = $('#allow-reviewer-search-conflict-override').prop('checked');
              $(this).prop('disabled', !(candidate && reviewerCandidateEffectivelySelectable(candidate, conflictOverrideChecked)));
            });
          }
          $('#assign-selected-search-reviewers').prop('disabled', selectedCount <= 0 || totalCount > AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments);
          $('#manual-reviewer-selection-status').text(
            selectedCount
              ? 'Selected ' + selectedCount + ' reviewer(s). Total after assignment: ' + totalCount + '/' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + '.'
              : 'No reviewers selected.'
          );
        };
        $('.manual-reviewer-candidate-row').off('click').on('click', function(event) {
          if ($(event.target).is('input, button, a')) return;
          var checkbox = $(this).find('.manual-reviewer-candidate');
          if (!checkbox.length || checkbox.prop('disabled')) return;
          checkbox.prop('checked', !checkbox.prop('checked')).trigger('change');
        });
        $('.manual-reviewer-candidate').off('change').on('change', function() {
          var selectedCount = $('.manual-reviewer-candidate:checked:not(:disabled)').length;
          if (activeAssignedCount + selectedCount > AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments) {
            $(this).prop('checked', false);
            setAutoAssignStatus('At most ' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + ' reviewers can be assigned. Uncheck another reviewer or remove an existing assignment first.', true);
          }
          updateManualReviewerSelectionState();
        });
        $('#allow-reviewer-search-conflict-override').off('change').on('change', updateManualReviewerSelectionState);
        $('#assign-selected-search-reviewers').off('click').on('click', function() {
          var button = $(this);
          var selectedTails = $('.manual-reviewer-candidate:checked:not(:disabled)').map(function() { return $(this).val(); }).get();
          if (!selectedTails.length) return;
          var selectedDueDateMillis = reviewerDueDateMillisFromInput();
          if (isNaN(selectedDueDateMillis)) {
            setAutoAssignStatus('Review due date must use YYYY-MM-DD format.', true);
            return;
          }
          setReviewerAssignmentButtonBusy(button);
          var attemptedAssignmentPayloads = selectedTails.map(function(tail) {
            var selectedCandidate = candidates.find(function(candidate) { return candidate.tail === tail; }) || {};
            return reviewerAssignmentEdgePayload(tail, signature, reviewerAssignmentOverrideLabel(selectedCandidate, signature));
          });
          var handleAssignmentError = function(error) {
            error = error || {};
            if (typeof error !== 'object') error = { message: String(error) };
            if (!error.assignmentPayload && !error.assignmentPayloads) error.assignmentPayloads = attemptedAssignmentPayloads;
            var message = reviewerAssignmentErrorMessage(error, 'Unable to assign selected reviewers.');
            setReviewerAssignmentProgress(button, message, true);
            restoreReviewerAssignmentButton(button);
          };
          withAutoAssignTimeout(
            Webfield2.api.getAll('/edges', { invitation: reviewerAssignmentInvitationId(), head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId, trash: true, stream: true }),
            45000,
            'Timed out loading current reviewer assignments. Reload the assignment page and try again.'
          ).then(function(currentAssignmentEdges) {
            var currentAssignedTails = _.uniq((currentAssignmentEdges || []).filter(function(edge) { return !edge.ddate; }).map(function(edge) { return edge.tail; }));
            var newTails = selectedTails.filter(function(tail) { return currentAssignedTails.indexOf(tail) < 0; });
            if (currentAssignedTails.length + newTails.length > AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments) {
              setReviewerAssignmentProgress(button, 'At most ' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + ' reviewers can be assigned. Uncheck a reviewer or remove an existing assignment first.', true);
              restoreReviewerAssignmentButton(button);
              return;
            }
            if (!newTails.length) {
              showReviewerAssignmentComplete(button, 'The selected reviewers are already assigned. Refreshing...');
              return;
            }
            var assignmentChain = newTails.reduce(function(chain, tail, index) {
              return chain.then(function() {
                setReviewerAssignmentProgress(button, 'Submitting reviewer assignment ' + (index + 1) + ' of ' + newTails.length + '...', false);
                var selectedCandidate = candidates.find(function(candidate) { return candidate.tail === tail; }) || {};
                return refreshReviewerSearchCandidateConflict(selectedCandidate, signature).then(function(refreshedCandidate) {
                  var overrideChecked = $('#allow-reviewer-search-conflict-override').prop('checked');
                  if (!reviewerCandidateEffectivelySelectable(refreshedCandidate, overrideChecked)) {
                    return $.Deferred().reject({
                      message: 'Reviewer ' + tail + ' is no longer eligible after refreshing conflict status.'
                    }).promise();
                  }
                  return postCheckedReviewerAssignmentEdge(tail, signature, reviewerAssignmentOverrideLabel(refreshedCandidate, signature), selectedDueDateMillis);
                });
              });
            }, Promise.resolve());
	    assignmentChain.then(function() {
              showReviewerAssignmentComplete(button, 'Assigned ' + newTails.length + ' reviewer(s).');
            }).catch(handleAssignmentError);
          }, handleAssignmentError);
        });
        updateManualReviewerSelectionState();
        });
      });
    });
      }).fail(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || error || 'Unable to search reviewers.';
    $('#manual-reviewer-search-results').html('<p class="text-danger">' + escapeAutoAssignHtml(message) + '</p>');
      });
    }
"""
