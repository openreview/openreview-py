AUTO_ASSIGN_REVIEWERS_TAB_JS = r"""    function submitAutoReviewerAssignments() {
      hideReviewerInviteForm();
      hideReviewerSearchPanel();
      hidePreviousReviewersPanel();
      $('#confirm-auto-assign-container').remove();
      $('#auto-assign-reviewers').prop('disabled', true).text('Checking reviewers...');
      $.when(
    getAutoAssignmentSignature(),
    getReviewerCandidateTails(),
    Webfield2.api.getAll('/edges', { invitation: reviewerAssignmentInvitationId(), head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId, trash: true, stream: true }),
    Webfield2.api.getAll('/edges', { invitation: AUTO_ASSIGN_CONFIG.reviewersAffinityScoreId, head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId })
      ).then(function(signature, reviewerCandidateTails, assignmentEdges, affinityEdges) {
    reviewerCandidateTails = reviewerCandidateTails || [];
    assignmentEdges = assignmentEdges || [];
    affinityEdges = affinityEdges || [];
    var assignedEdgesByTail = assignmentEdges.reduce(function(byTail, edge) {
      if (edge.tail && !byTail[edge.tail]) byTail[edge.tail] = edge;
      return byTail;
    }, {});
    var assignedReviewers = _.uniq(assignmentEdges.filter(function(edge) { return !edge.ddate; }).map(function(edge) { return edge.tail; }).filter(function(tail) { return !!tail; }));
    var neededAssignments = AUTO_ASSIGN_CONFIG.numberOfReviewers;
    var affinityTails = affinityEdges.map(function(edge) { return edge.tail; });
    var activeReviewerTailSet = new Set(reviewerCandidateTails || []);
    var tails = _.uniq(affinityTails.concat(reviewerCandidateTails).filter(function(tail) {
      return tail && !assignedReviewers.includes(tail);
    }));
    var allDisplayTails = _.uniq(assignedReviewers.concat(tails));
    if (!allDisplayTails.length) {
      setAutoAssignStatus('No reviewers were found. Please choose reviewers manually or invite a new reviewer.', true);
      return;
    }
    $.when(
      getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersConflictId, AUTO_ASSIGN_CONFIG.noteId, tails),
      getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersPendingReviewsId, null, tails),
      getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersCustomMaxPapersId, null, tails),
      getReviewerAssignmentHistoryByTail(tails),
      getProfilesById(allDisplayTails),
      getReviewerStatsByTail(allDisplayTails),
      getExpertReviewerIds()
    ).then(function(conflictsByTail, pendingByTail, maxPapersByTail, assignmentHistoryByTail, profilesById, statsByTail, expertReviewerIds) {
      var affinityByTail = affinityEdges.reduce(function(byTail, edge) {
        byTail[edge.tail] = Math.max(byTail[edge.tail] === undefined ? -Infinity : byTail[edge.tail], getEdgeWeight(edge, -Infinity));
        return byTail;
      }, {});
      var getAutoAssignReviewerName = function(profile, fallback) {
        var content = profile && profile.content || {};
        var names = content.names || [];
        var preferredName = names.find(function(name) { return name && name.preferred; }) || names[0] || {};
        return content.preferredName || preferredName.fullname || getProfileName(profile, fallback);
      };
      var candidateForTail = function(tail, isAssigned) {
        var profile = profilesById[tail] || null;
        var assignmentEdge = assignedEdgesByTail[tail] || {};
        var configuredCooldownUntil = AUTO_ASSIGN_CONFIG.reviewerAssignmentCooldownUntilByTail && AUTO_ASSIGN_CONFIG.reviewerAssignmentCooldownUntilByTail[tail] || 0;
        var cooldownStatus = configuredCooldownUntil && configuredCooldownUntil > Date.now()
          ? { blocked: true, until: configuredCooldownUntil }
          : getReviewerCooldownStatus(assignmentHistoryByTail[tail] || []);
        var availability = getPaperScopedReviewerAvailability(tail);
        return {
          tail: tail,
          edgeId: assignmentEdge.id,
          name: getAutoAssignReviewerName(profile, tail),
          email: getProfileEmails(profile, tail),
          affiliation: getProfileAffiliation(profile),
          assigned: !!isAssigned,
          isExpertReviewer: expertReviewerIds.has(tail),
          ratingStats: statsByTail[tail] || unavailableReviewerStats('reviewer statistics missing from lookup result'),
          affinity: affinityByTail[tail] === undefined ? 0 : affinityByTail[tail],
          hasAffinity: affinityByTail[tail] !== undefined,
          randomOrder: Math.random(),
          conflictWeight: getEdgeWeight((conflictsByTail[tail] || [])[0], 0),
          conflictEdge: (conflictsByTail[tail] || [])[0] || null,
          availability: availability,
          availabilityAvailable: availability.state === 'available',
          cooldownBlocked: cooldownStatus.blocked,
          cooldownUntil: cooldownStatus.until,
          activePaperLoad: getEdgeWeight((pendingByTail[tail] || [])[0], 0),
          maxPapers: getEdgeWeight((maxPapersByTail[tail] || [])[0], AUTO_ASSIGN_CONFIG.reviewersMaxPapers),
          active: activeReviewerTailSet.has(tail)
        };
      };
      var assignedCandidates = assignedReviewers.map(function(tail) {
        return candidateForTail(tail, true);
      });
      var remainingAssignmentSlots = Math.max(0, AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments - assignedCandidates.length);
      var defaultNewSelectionCount = Math.min(
        Math.max(0, AUTO_ASSIGN_CONFIG.numberOfReviewers - assignedCandidates.length),
        remainingAssignmentSlots
      );
      var candidates = tails.map(function(tail) {
        return candidateForTail(tail, false);
      }).sort(function(a, b) {
        if (b.affinity !== a.affinity) return b.affinity - a.affinity;
        return a.randomOrder - b.randomOrder;
      });
      var displayedCandidates = candidates.slice(0, Math.max(AUTO_ASSIGN_CONFIG.candidateDisplayLimit, neededAssignments));
      displayedCandidates.forEach(function(candidate) {
        candidate.eligibility = reviewerEligibilityStatus(candidate);
      });
      var eligibleCandidates = displayedCandidates.filter(function(candidate) {
        return candidate.classification && candidate.classification.severity === 'eligible';
      });
      var conflictCandidates = displayedCandidates.filter(function(candidate) {
        return candidate.classification && candidate.classification.severity === 'warning_conflict';
      });
      var authorConflictCandidates = displayedCandidates.filter(function(candidate) {
        return candidate.classification && candidate.classification.severity === 'author_conflict';
      });
      var unavailableCandidates = displayedCandidates.filter(function(candidate) {
        return candidate.classification && ['eligible', 'warning_conflict', 'author_conflict'].indexOf(candidate.classification.severity) < 0;
      });
      if (!assignedCandidates.length && !eligibleCandidates.length && !conflictCandidates.length && !authorConflictCandidates.length && !unavailableCandidates.length) {
        setAutoAssignStatus('No reviewers were found. Please choose reviewers manually or invite a new reviewer.', true);
        return;
      }
      var affinityMessage = affinityEdges.length ? 'Reviewers are ranked by affinity score; missing affinity scores are treated as 0.' : 'No affinity scores were found, so reviewers are shown with affinity 0 in randomized order.';
      var capacityMessage = assignedCandidates.length >= AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments ?
        'This paper already has ' + assignedCandidates.length + ' assigned reviewers. Remove an assignment manually before adding another reviewer.' :
        'You can add up to ' + remainingAssignmentSlots + ' more reviewer(s), for at most ' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + ' total.';
      setAutoAssignStatus('Current reviewers: ' + assignedCandidates.length + '/' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + '. Needed to reach release threshold: ' + Math.max(0, AUTO_ASSIGN_CONFIG.numberOfReviewers - assignedCandidates.length) + '. ' + affinityMessage, false);
      $('#confirm-auto-assign-container').remove();
      var renderAutoAssignRows = function(rows, options) {
        options = options || {};
        if (!rows.length) {
          return '<tr><td colspan="7" class="text-muted">' + escapeAutoAssignHtml(options.emptyMessage || 'No reviewers in this section.') + '</td></tr>';
        }
        return rows.map(function(candidate, index) {
          var isOpenReviewConflict = candidate.classification && candidate.classification.severity === 'warning_conflict';
          var isAuthorConflict = candidate.classification && candidate.classification.severity === 'author_conflict';
          var conflictOverrideChecked = REVIEWER_AUTO_CONFLICT_OVERRIDE_ENABLED;
          var selectable = options.selectable || (options.conflictSelectable && reviewerCandidateEffectivelySelectable(candidate, conflictOverrideChecked));
          var checked = options.current ? ' checked' : (selectable && !isOpenReviewConflict && index < defaultNewSelectionCount ? ' checked' : '');
          var disabled = options.current || !selectable || isAuthorConflict || remainingAssignmentSlots <= 0 ? ' disabled' : '';
          var affinity = candidate.hasAffinity ? candidate.affinity : 0;
          var title = candidate.name === candidate.tail ? candidate.tail : candidate.name + ' (' + candidate.tail + ')';
          var reviewerProfileUrl = '/profile?id=' + encodeURIComponent(candidate.tail);
          var reviewerDisplayName = candidate.name || candidate.tail;
          var eligibility = candidate.eligibility || reviewerEligibilityStatus(candidate);
          var rowClass = options.current ? 'active' : '';
          if (isOpenReviewConflict) rowClass += ' warning';
          if (isAuthorConflict) rowClass += ' danger';
          var rowStyle = selectable ? 'cursor: pointer;' : (candidate.classification && candidate.classification.severity === 'unavailable' ? 'color: #777; background: #f7f7f7;' : '');
          return '<tr' + (rowClass ? ' class="' + rowClass + '"' : '') + reviewerCandidateRowAttributes(candidate, conflictOverrideChecked) + (rowStyle ? ' style="' + rowStyle + '"' : '') + '>' +
            '<td style="width: 44px; min-width: 44px; max-width: 44px; text-align: center;"><input type="checkbox" class="auto-assign-candidate' + (!options.current && selectable ? ' auto-assign-selectable' : '') + '" value="' + escapeAutoAssignHtml(candidate.tail) + '"' + checked + disabled + '></td>' +
            '<td style="width: 260px; min-width: 260px; max-width: 260px; white-space: normal; overflow-wrap: anywhere; word-break: break-word;"><strong><a href="' + reviewerProfileUrl + '" target="_blank" rel="noopener noreferrer" title="' + escapeAutoAssignHtml(title) + '">' + escapeAutoAssignHtml(reviewerDisplayName) + '</a></strong></td>' +
            '<td>' + escapeAutoAssignHtml(candidate.affiliation || '') + '</td>' +
            '<td>' + escapeAutoAssignHtml(reviewerStatsSummary(candidate.ratingStats)) + '</td>' +
            '<td>' + escapeAutoAssignHtml(candidate.hasAffinity ? affinity : '0 (missing)') + '</td>' +
            '<td>' + escapeAutoAssignHtml(candidate.activePaperLoad) + ' / ' + escapeAutoAssignHtml(candidate.maxPapers) + '</td>' +
            '<td>' + formatReviewerConflictCell(candidate, options.current ? 'Current reviewer' : '') + '</td>' +
            '</tr>';
        }).join('');
      };
      var renderAutoAssignSection = function(title, rows, options) {
        options = options || {};
        var table =
          '<div class="table-responsive" style="max-height: 520px; overflow-y: auto; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd;">' +
            '<table class="table table-condensed" style="margin-bottom: 0;">' +
              '<thead><tr><th style="width: 44px; min-width: 44px; max-width: 44px;">Select</th><th style="width: 260px; min-width: 260px; max-width: 260px;">Reviewer</th><th>Affiliation</th><th>Rating / Timeliness</th><th>Affinity</th><th>Load</th><th>Conflicts</th></tr></thead><tbody>' +
                renderAutoAssignRows(rows, options) +
              '</tbody></table>' +
          '</div>';
        if (options.collapsed) {
          return '<details style="margin-top: 12px;">' +
            '<summary><strong>' + escapeAutoAssignHtml(title) + '</strong> <span class="text-muted">(' + rows.length + ')</span></summary>' +
            table +
          '</details>';
        }
        if (!title) return table;
        return '<h4 style="margin: 12px 15px 8px;">' + escapeAutoAssignHtml(title) + ' <span class="text-muted">(' + rows.length + ')</span></h4>' + table;
      };
      $('#auto-assign-status').after(
        '<div id="confirm-auto-assign-container" style="max-width: 1100px; margin: 12px auto 0;">' +
        '<div class="panel panel-default" style="text-align: left;">' +
        '<div class="panel-heading"><strong>Auto-assign reviewers</strong></div>' +
        '<div class="panel-body">' +
          '<p class="text-muted">Showing the top ' + displayedCandidates.length + ' affinity-score reviewer matches. Current reviewers are listed first; ineligible matches are collapsed by default.</p>' +
          '<div class="form-inline" style="margin-bottom: 10px;">' +
            '<label for="reviewers-to-add" style="margin-right: 8px;">Reviewers to add</label>' +
            '<input id="reviewers-to-add" class="form-control input-sm" type="number" min="' + (remainingAssignmentSlots > 0 ? 1 : 0) + '" max="' + remainingAssignmentSlots + '" value="' + defaultNewSelectionCount + '" style="width: 90px;"> ' +
            '<span class="text-muted">Timeliness order: ' + escapeAutoAssignHtml((AUTO_ASSIGN_CONFIG.timelinessOrder || []).join(' / ')) + '. Rating scores: ' + escapeAutoAssignHtml(reviewerRatingHelpText()) + '.</span>' +
          '</div>' +
        '</div>' +
        renderAutoAssignSection('Current reviewers', assignedCandidates, { current: true, emptyMessage: 'No current reviewers.' }) +
        renderAutoAssignSection('Eligible reviewers', eligibleCandidates, { selectable: true, emptyMessage: 'No eligible reviewer matches.' }) +
        (conflictCandidates.length ? '<details class="panel panel-warning" style="text-align: left;" open><summary class="panel-heading" style="display: block; cursor: pointer;"><strong>OpenReview conflict warnings</strong> <span class="text-muted">(' + conflictCandidates.length + ')</span></summary><div class="panel-body" style="padding-bottom: 0;"><div class="checkbox" style="margin-top: 0;"><label><input id="allow-reviewer-auto-conflict-override" type="checkbox"' + (REVIEWER_AUTO_CONFLICT_OVERRIDE_ENABLED ? ' checked' : '') + '> Allow AE/EIC override for selected OpenReview conflict rows.</label></div></div>' + renderAutoAssignSection('', conflictCandidates, { conflictSelectable: true, emptyMessage: 'No OpenReview conflict warnings.' }) + '</details>' : '') +
        (authorConflictCandidates.length ? '<details class="panel panel-danger" style="text-align: left;" open><summary class="panel-heading" style="display: block; cursor: pointer;"><strong>Author conflicts</strong> <span class="text-muted">(' + authorConflictCandidates.length + ')</span></summary><div class="panel-body" style="padding-bottom: 0;">These reviewers are listed as paper authors or author-declared conflicts and cannot be selected.</div>' + renderAutoAssignSection('', authorConflictCandidates, { emptyMessage: 'No author conflicts.' }) + '</details>' : '') +
        (unavailableCandidates.length ? '<details class="panel panel-default" style="text-align: left; opacity: 0.82;"><summary class="panel-heading" style="display: block; cursor: pointer;"><strong>Not selectable reviewers</strong> <span class="text-muted">(' + unavailableCandidates.length + ')</span></summary>' + renderAutoAssignSection('', unavailableCandidates, { emptyMessage: 'No not-selectable reviewers.' }) + '</details>' : '') +
        '<div id="selected-reviewer-stat-summary" class="small text-muted" style="padding: 8px 15px;"></div>' +
        '</div>' +
        '<p class="text-center" style="margin-top: 8px;">' +
        reviewerDueDateInputHtml('auto-reviewer-due-date') +
        '<button id="confirm-auto-assign" type="button" class="btn btn-primary"' + (remainingAssignmentSlots <= 0 ? ' disabled' : '') + '>Assign Selected Reviewers</button>' +
        '<span class="reviewer-assignment-button-status text-muted" style="margin-left: 8px;"></span>' +
        '</p>' +
        '</div>'
      );
      var updateSelectedReviewerStatSummary = function() {
        var selectedTails = $('.auto-assign-selectable:checked:not(:disabled)').map(function() { return $(this).val(); }).get();
        var selectedCandidates = displayedCandidates.filter(function(candidate) {
          return selectedTails.includes(candidate.tail);
        });
        if (!selectedCandidates.length) {
          $('#selected-reviewer-stat-summary').text('No new reviewers selected.');
          return;
        }
        $('#selected-reviewer-stat-summary').html(
          '<strong>Selected reviewer stats:</strong> ' +
          selectedCandidates.map(function(candidate) {
            return escapeAutoAssignHtml(candidate.name + ': ' + reviewerStatsSummary(candidate.ratingStats));
          }).join('; ')
        );
      };
      $('#reviewers-to-add').off('change input').on('change input', function() {
        var requested = Math.max(0, Math.min(remainingAssignmentSlots, Number($(this).val()) || 0));
        $('.auto-assign-selectable:not(:disabled)').prop('checked', false);
        $('.auto-assign-selectable:not(:disabled)').slice(0, requested).prop('checked', true);
        updateAutoAssignSelectionState(false);
        updateSelectedReviewerStatSummary();
      });
      var updateAutoAssignSelectionState = function(showError) {
        $('.auto-assign-candidate').each(function() {
          var checkbox = $(this);
          var row = checkbox.closest('tr');
          var overrideAllowed = row.attr('data-reviewer-override-allowed') === 'true';
          if (overrideAllowed) {
            checkbox.toggleClass('auto-assign-selectable', REVIEWER_AUTO_CONFLICT_OVERRIDE_ENABLED);
            row.toggleClass('text-muted', !REVIEWER_AUTO_CONFLICT_OVERRIDE_ENABLED);
            if (!REVIEWER_AUTO_CONFLICT_OVERRIDE_ENABLED) checkbox.prop('checked', false).prop('disabled', true);
          }
        });
        var selectedNewCount = $('.auto-assign-selectable:checked:not(:disabled)').length;
        var totalSelectedCount = assignedCandidates.length + selectedNewCount;
        if (totalSelectedCount >= AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments) {
          $('.auto-assign-selectable:not(:checked):not(:disabled)').prop('disabled', true);
        } else {
          $('.auto-assign-selectable:not(:checked)').prop('disabled', false);
          $('.auto-assign-candidate:not(.auto-assign-selectable):not(:checked)').prop('disabled', true);
        }
        if (showError && totalSelectedCount > AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments) {
          setAutoAssignStatus('At most ' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + ' reviewers can be assigned. Uncheck a reviewer or use manual assignment to remove an existing assignment.', true);
        }
      };
      $('.auto-assign-candidate').off('change').on('change', function() {
        var selectedNewCount = $('.auto-assign-selectable:checked:not(:disabled)').length;
        if (assignedCandidates.length + selectedNewCount > AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments) {
          $(this).prop('checked', false);
          setAutoAssignStatus('At most ' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + ' reviewers can be assigned. Uncheck another reviewer or remove an existing assignment manually first.', true);
        } else {
          setAutoAssignStatus('Current reviewers: ' + assignedCandidates.length + '/' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + '. Needed to reach release threshold: ' + Math.max(0, AUTO_ASSIGN_CONFIG.numberOfReviewers - assignedCandidates.length) + '. ' + affinityMessage, false);
        }
        updateAutoAssignSelectionState(false);
        updateSelectedReviewerStatSummary();
      });
      $('#allow-reviewer-auto-conflict-override').off('change').on('change', function() {
        REVIEWER_AUTO_CONFLICT_OVERRIDE_ENABLED = $(this).prop('checked');
        updateAutoAssignSelectionState(false);
        updateSelectedReviewerStatSummary();
      });
      updateAutoAssignSelectionState(false);
      updateSelectedReviewerStatSummary();
      $('#confirm-auto-assign').off('click').on('click', function() {
        if (assignedCandidates.length >= AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments) {
          setAutoAssignStatus('This paper already has ' + assignedCandidates.length + ' assigned reviewers. Use manual assignment to remove an existing assignment before adding another reviewer.', true);
          return;
        }
        var selectedDueDateMillis = reviewerDueDateMillisFromInput('auto-reviewer-due-date');
        if (isNaN(selectedDueDateMillis)) {
          setAutoAssignStatus('Review due date must use YYYY-MM-DD format.', true);
          return;
        }
        setReviewerAssignmentButtonBusy($('#confirm-auto-assign'));
        var handleAssignmentError = function(error) {
          var message = reviewerAssignmentErrorMessage(error, 'Unable to auto-assign reviewers.');
          setReviewerAssignmentProgress($('#confirm-auto-assign'), message, true);
          restoreReviewerAssignmentButton($('#confirm-auto-assign'));
        };
        try {
          var selectedTails = $('.auto-assign-selectable:checked:not(:disabled)').map(function() { return $(this).val(); }).get();
          var initiallySelectedCandidates = displayedCandidates.filter(function(candidate) {
            return selectedTails.includes(candidate.tail);
          });
          withAutoAssignTimeout(
            Webfield2.api.getAll('/edges', { invitation: reviewerAssignmentInvitationId(), head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId, trash: true, stream: true }),
            45000,
            'Timed out loading current reviewer assignments. Reload the assignment page and try again.'
          ).then(function(currentAssignmentEdges) {
            var currentAssignedTails = _.uniq((currentAssignmentEdges || []).filter(function(edge) { return !edge.ddate; }).map(function(edge) { return edge.tail; }));
            var selectedCandidates = initiallySelectedCandidates.filter(function(candidate) {
              return !currentAssignedTails.includes(candidate.tail);
            });
            if (currentAssignedTails.length >= AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments) {
              setReviewerAssignmentProgress($('#confirm-auto-assign'), 'This paper already has ' + currentAssignedTails.length + ' assigned reviewers. Use manual assignment to remove an existing assignment before adding another reviewer.', true);
              restoreReviewerAssignmentButton($('#confirm-auto-assign'));
              return;
            }
            if (currentAssignedTails.length + selectedCandidates.length > AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments) {
              setReviewerAssignmentProgress($('#confirm-auto-assign'), 'At most ' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + ' reviewers can be assigned. Uncheck a reviewer or use manual assignment to remove an existing assignment.', true);
              restoreReviewerAssignmentButton($('#confirm-auto-assign'));
              return;
            }
            if (!selectedCandidates.length) {
              showReviewerAssignmentComplete($('#confirm-auto-assign'), 'The selected reviewers are already assigned.');
              return;
            }
	    var assignmentChain = selectedCandidates.reduce(function(chain, candidate, index) {
	      return chain.then(function() {
	        setReviewerAssignmentProgress($('#confirm-auto-assign'), 'Submitting reviewer assignment ' + (index + 1) + ' of ' + selectedCandidates.length + '...', false);
	        return postCheckedReviewerAssignmentEdge(candidate.tail, signature, reviewerAssignmentOverrideLabel(candidate, signature), selectedDueDateMillis);
	      });
	    }, Promise.resolve());
	    assignmentChain.then(function() {
              showReviewerAssignmentComplete($('#confirm-auto-assign'), 'Assigned ' + selectedCandidates.length + ' reviewer(s).');
            }).catch(handleAssignmentError);
          }, handleAssignmentError);
        } catch (error) {
          handleAssignmentError(error);
        }
      });
    });
      }).fail(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || error || 'Unable to auto-assign reviewers.';
    setAutoAssignStatus(message, true);
      }).always(function() {
    $('#auto-assign-reviewers').prop('disabled', false).text('Auto-assign Reviewers');
      });
    }
"""
