PREVIOUS_REVIEWERS_TAB_JS = r"""    function hasPreviousSubmissionReference() {
      var previousId = String(AUTO_ASSIGN_CONFIG.previousSubmissionId || '').trim();
      var previousNumber = String(AUTO_ASSIGN_CONFIG.previousSubmissionNumber || '').trim();
      var previousList = String(AUTO_ASSIGN_CONFIG.previousSubmissionList || '').trim();
      return !!previousId || (!!previousNumber && previousNumber.toUpperCase() !== 'N/A') || !!previousList;
    }

    function previousSubmissionIdFromList() {
      var match = String(AUTO_ASSIGN_CONFIG.previousSubmissionList || '').match(/forum\?id=([A-Za-z0-9_-]+)/);
      return match && match[1] || '';
    }

    function previousSubmissionNumberFromList() {
      var match = String(AUTO_ASSIGN_CONFIG.previousSubmissionList || '').match(/Paper\s+([0-9]+)/);
      return match && match[1] || '';
    }

    function resolvePreviousSubmissionForReviewerAssignment() {
      var previousId = String(AUTO_ASSIGN_CONFIG.previousSubmissionId || previousSubmissionIdFromList()).trim();
      if (previousId) {
    return Webfield2.api.get('/notes', { id: previousId }).then(function(result) {
      return result && result.notes && result.notes[0] || null;
    }, function() {
      return null;
    });
      }
      var previousNumber = String(AUTO_ASSIGN_CONFIG.previousSubmissionNumber || previousSubmissionNumberFromList()).trim();
      if (!previousNumber || previousNumber.toUpperCase() === 'N/A' || !/^\d+$/.test(previousNumber)) {
    return $.Deferred().resolve(null).promise();
      }
      return Webfield2.api.get('/notes', {
    invitation: AUTO_ASSIGN_CONFIG.venueId + '/-/Submission',
    number: Number(previousNumber),
    domain: AUTO_ASSIGN_CONFIG.venueId
      }).then(function(result) {
    return result && result.notes && result.notes[0] || null;
      }, function() {
    return null;
      });
    }

    function loadPreviousReviewerAssignments(previousSubmission) {
      if (!previousSubmission || !previousSubmission.id) {
    return $.Deferred().resolve([]).promise();
      }
      var invitationIds = [
    AUTO_ASSIGN_CONFIG.venueId + '/Paper' + previousSubmission.number + '/Reviewers/-/Assignment',
    reviewerAssignmentInvitationId(),
    AUTO_ASSIGN_CONFIG.venueId + '/Reviewers/-/Archived_Assignment'
      ];
      var chain = invitationIds.reduce(function(promise, invitationId) {
    return promise.then(function(previousReviewerIds) {
      return Webfield2.api.getAll('/edges', {
        invitation: invitationId,
        head: previousSubmission.id,
        domain: AUTO_ASSIGN_CONFIG.venueId
      }).then(function(edges) {
        (edges || []).forEach(function(edge) {
          if (edge.tail && edge.tail.charAt(0) === '~' && !edge.ddate && previousReviewerIds.indexOf(edge.tail) < 0) {
            previousReviewerIds.push(edge.tail);
          }
        });
        return previousReviewerIds;
      }, function() {
        return previousReviewerIds;
      });
    });
      }, $.Deferred().resolve([]).promise());
      return chain;
    }

    function contentFieldValue(note, fieldName) {
      var field = note && note.content && note.content[fieldName];
      if (!field) return '';
      return typeof field.value === 'undefined' ? field : field.value;
    }

    function reviewerAnonIdFromDecisionField(fieldName) {
      return String(fieldName || '').replace('resubmission_auto_assign_reviewer_', '').replace('reviewer_', '');
    }

    function reviewerAnonIdFromDecisionCheckboxValue(value) {
      var match = String(value || '').match(/Reviewer\s+([^:\s]+)/);
      return match && match[1] || '';
    }

    function isTruthyDecisionSelection(value) {
      if (_.isArray(value)) return !!value.length;
      if (typeof value === 'string') {
        var normalized = value.trim();
        return !!normalized && ['false', 'False', '0', 'No'].indexOf(normalized) < 0;
      }
      return value === true || value === 1;
    }

    function isTruthyReviewerRatingSelection(value) {
      if (_.isArray(value)) return !!value.length;
      if (typeof value === 'string') {
        var normalized = value.trim().toLowerCase();
        return !!normalized && ['false', '0', 'no'].indexOf(normalized) < 0;
      }
      return value === true || value === 1;
    }

    function reviewerAnonIdFromRatingInvitation(invitationId) {
      var match = String(invitationId || '').match(/\/Reviewer_([^/]+)\/-\/Rating$/);
      return match && match[1] || '';
    }

    function selectedPreviousReviewerAnonIds(previousDecision) {
      if (!previousDecision) return [];
      var selected = [];
      var checkboxValue = contentFieldValue(previousDecision, 'reviewers');
      var checkboxValues = _.isArray(checkboxValue) ? checkboxValue : (checkboxValue ? [checkboxValue] : []);
      checkboxValues.forEach(function(value) {
        var anonId = reviewerAnonIdFromDecisionCheckboxValue(value);
        if (anonId && selected.indexOf(anonId) < 0) selected.push(anonId);
      });
      _.forEach(previousDecision.content || {}, function(field, fieldName) {
        if (fieldName === 'reviewer_auto_assignment') return;
        if (fieldName.indexOf('reviewer_') !== 0 && fieldName.indexOf('resubmission_auto_assign_reviewer_') !== 0) return;
        var value = field && typeof field.value !== 'undefined' ? field.value : field;
        if (isTruthyDecisionSelection(value)) {
          var anonId = reviewerAnonIdFromDecisionField(fieldName);
          if (anonId && selected.indexOf(anonId) < 0) selected.push(anonId);
        }
      });
      return selected;
    }

    function loadSelectedPreviousReviewerRatingAssignments(previousSubmission) {
      if (!previousSubmission || !previousSubmission.id || !previousSubmission.number) {
    return $.Deferred().resolve({ profileIds: [], hasReviewerRatingSelectionField: false }).promise();
      }
      return Webfield2.api.getAll('/notes', {
      forum: previousSubmission.id,
      domain: AUTO_ASSIGN_CONFIG.venueId
    }).then(null, function() {
      return [];
    }).then(function(notes) {
    var selectedProfileIds = [];
    var hasReviewerRatingSelectionField = false;
    (notes || []).forEach(function(note) {
      var invitationId = note && note.invitations && note.invitations[0] || '';
      if (note.ddate || invitationId.indexOf('/-/Rating') < 0) return;
      var selectionField = note.content && note.content.resubmission_auto_assignment;
      if (!selectionField) return;
      hasReviewerRatingSelectionField = true;
      if (!isTruthyReviewerRatingSelection(contentFieldValue(note, 'resubmission_auto_assignment'))) return;
      var profileId = contentFieldValue(note, 'reviewer_profile_id');
      if (profileId && selectedProfileIds.indexOf(profileId) < 0) selectedProfileIds.push(profileId);
    });
    var selectedRatingNotes = (notes || []).filter(function(note) {
      var invitationId = note && note.invitations && note.invitations[0] || '';
      return !note.ddate && invitationId.indexOf('/-/Rating') >= 0 &&
        note.content && note.content.resubmission_auto_assignment &&
        isTruthyReviewerRatingSelection(contentFieldValue(note, 'resubmission_auto_assignment')) &&
        !contentFieldValue(note, 'reviewer_profile_id');
    });
    var chain = selectedRatingNotes.reduce(function(promise, note) {
      return promise.then(function(profileIds) {
        var anonId = contentFieldValue(note, 'reviewer_anon_id') || reviewerAnonIdFromRatingInvitation(note.invitations && note.invitations[0]);
        return resolvePreviousReviewerProfileId(previousSubmission, anonId).then(function(profileId) {
          if (profileId && profileIds.indexOf(profileId) < 0) profileIds.push(profileId);
          return profileIds;
        });
      });
    }, $.Deferred().resolve(selectedProfileIds).promise());
    return chain.then(function(profileIds) {
      return {
        profileIds: profileIds,
        hasReviewerRatingSelectionField: hasReviewerRatingSelectionField
      };
    });
      }, function() {
    return { profileIds: [], hasReviewerRatingSelectionField: false };
      });
    }

    function resolvePreviousReviewerProfileId(previousSubmission, previousAnonId) {
      if (!previousSubmission || !previousSubmission.number || !previousAnonId) {
    return $.Deferred().resolve('').promise();
      }
      return Webfield2.api.get('/groups', {
    id: AUTO_ASSIGN_CONFIG.venueId + '/Paper' + previousSubmission.number + '/Reviewer_' + previousAnonId,
    limit: 1,
    select: 'members'
      }).then(function(result) {
    var groups = result && result.groups || [];
    var members = groups[0] && groups[0].members || [];
    return members[0] || '';
      }, function() {
    return '';
      });
    }

    function reviewerAnonIdFromReviewSignature(signature) {
      var match = String(signature || '').match(/\/Reviewer_([^/]+)/);
      return match && match[1] || '';
    }

    function isReviewerScoringInputAnonId(anonId) {
      return String(anonId || '') === 'Scoring_Input';
    }

    function previousReviewerContinuityNumberForTail(tail) {
      var row = reviewerContinuityRowForTail(tail);
      if (!row) return '';
      var stableNumber = row.stable_number || String(row.stable_label || '').replace(/[^0-9]/g, '');
      return stableNumber ? 'Reviewer ' + stableNumber : '';
    }

    function loadPreviousReviewerMetadata(previousSubmission, previousReviewerIds) {
      if (!previousSubmission || !previousSubmission.id || !previousSubmission.number || !previousReviewerIds.length) {
    return $.Deferred().resolve({}).promise();
      }
      return $.when(
    Webfield2.api.getAll('/groups', {
      prefix: AUTO_ASSIGN_CONFIG.venueId + '/Paper' + previousSubmission.number + '/Reviewer_',
      domain: AUTO_ASSIGN_CONFIG.venueId,
      select: 'id,members'
    }).then(null, function() {
      return [];
    }),
    Webfield2.api.getAll('/notes', {
      forum: previousSubmission.id,
      domain: AUTO_ASSIGN_CONFIG.venueId
    }).then(null, function() {
      return [];
    })
      ).then(function(groups, notes) {
    var anonByTail = {};
    (groups || []).forEach(function(group) {
      var anonId = reviewerAnonIdFromReviewSignature(group && group.id);
      if (!anonId || isReviewerScoringInputAnonId(anonId)) return;
      (group && group.members || []).forEach(function(member) {
        if (member && member.charAt(0) === '~' && !anonByTail[member]) anonByTail[member] = anonId;
      });
    });
    var recommendationByAnon = {};
    (notes || []).forEach(function(note) {
      var invitationId = note && note.invitations && note.invitations[0] || '';
      if (note.ddate || invitationId !== AUTO_ASSIGN_CONFIG.venueId + '/Paper' + previousSubmission.number + '/-/Review') return;
      var anonId = '';
      (note.signatures || []).some(function(signature) {
        anonId = reviewerAnonIdFromReviewSignature(signature);
        return !!anonId;
      });
      if (!anonId || isReviewerScoringInputAnonId(anonId)) return;
      recommendationByAnon[anonId] = contentFieldValue(note, 'recommendation_for_acceptance') || 'No recommendation recorded';
    });
    return (previousReviewerIds || []).reduce(function(metadataByTail, tail) {
      var previousAnonId = anonByTail[tail] || '';
      metadataByTail[tail] = {
        previousAnonId: previousAnonId,
        continuityNumber: previousReviewerContinuityNumberForTail(tail),
        previousRecommendation: previousAnonId && recommendationByAnon[previousAnonId] || 'No recommendation recorded'
      };
      return metadataByTail;
    }, {});
      });
    }

    function loadSelectedPreviousReviewerAssignments(previousSubmission) {
      if (!previousSubmission || !previousSubmission.id || !previousSubmission.number) {
    return $.Deferred().resolve([]).promise();
      }
      return loadSelectedPreviousReviewerRatingAssignments(previousSubmission).then(function(ratingSelection) {
    if (ratingSelection.hasReviewerRatingSelectionField) {
      return ratingSelection.profileIds || [];
    }
    return Webfield2.api.getAll('/notes', {
    forum: previousSubmission.id,
    invitation: AUTO_ASSIGN_CONFIG.venueId + '/Paper' + previousSubmission.number + '/-/Decision',
    domain: AUTO_ASSIGN_CONFIG.venueId
      }).then(function(decisions) {
    var eligibleRecommendations = [
      'Accept after minor revisions',
      'Accept with minor revision',
      'Reject with encouragement to resubmit'
    ];
    var previousDecision = (decisions || []).find(function(decision) {
      return !decision.ddate && eligibleRecommendations.indexOf(contentFieldValue(decision, 'recommendation')) >= 0;
    });
    var selectedAnonIds = selectedPreviousReviewerAnonIds(previousDecision);
    var chain = selectedAnonIds.reduce(function(promise, anonId) {
      return promise.then(function(profileIds) {
        return resolvePreviousReviewerProfileId(previousSubmission, anonId).then(function(profileId) {
          if (profileId && profileIds.indexOf(profileId) < 0) profileIds.push(profileId);
          return profileIds;
        });
      });
    }, $.Deferred().resolve([]).promise());
    return chain;
      }, function() {
    return [];
      });
      });
    }

    function hidePreviousReviewersPanel() {
      $('#previous-reviewers-container').hide();
      $('#previous-reviewers-results').empty();
      setAutoAssignStatus('', false);
    }

    function showPreviousReviewersPanel() {
      hideReviewerInviteForm();
      hideReviewerSearchPanel();
      $('#confirm-auto-assign-container').remove();
      $('#previous-reviewers-container').show();
      $('#previous-reviewers-results').html('<p class="text-muted">Looking up previous reviewer assignments...</p>');
      setAutoAssignStatus('', false);
      var panel = $('#previous-reviewers-container')[0];
      if (panel && panel.scrollIntoView) panel.scrollIntoView({ block: 'start' });

      if (!hasPreviousSubmissionReference()) {
    $('#previous-reviewers-results').html('<p class="text-danger">This paper is not marked as a JMLR resubmission.</p>');
    return;
      }

      $.when(
    getAutoAssignmentSignature(),
    resolvePreviousSubmissionForReviewerAssignment(),
    Webfield2.api.getAll('/edges', { invitation: reviewerAssignmentInvitationId(), head: AUTO_ASSIGN_CONFIG.noteId, domain: AUTO_ASSIGN_CONFIG.venueId, trash: true, stream: true })
      ).then(function(signature, previousSubmission, currentAssignmentEdges) {
    currentAssignmentEdges = currentAssignmentEdges || [];
    if (!previousSubmission) {
      $('#previous-reviewers-results').html('<p class="text-danger">No previous JMLR submission could be resolved.</p>');
      return;
    }
    $.when(
      loadPreviousReviewerAssignments(previousSubmission),
      loadSelectedPreviousReviewerAssignments(previousSubmission)
    ).then(function(previousReviewerIds, selectedPreviousReviewerIds) {
      previousReviewerIds = previousReviewerIds || [];
      selectedPreviousReviewerIds = selectedPreviousReviewerIds || [];
      if (!previousReviewerIds.length) {
        $('#previous-reviewers-results').html('<p class="text-danger">No previous reviewer assignments were found for Paper ' + escapeAutoAssignHtml(previousSubmission.number) + '.</p>');
        return;
      }
      var currentAssignedTails = _.uniq(currentAssignmentEdges.filter(function(edge) {
        return edge.tail && !edge.ddate;
      }).map(function(edge) { return edge.tail; }));
      var assignableReviewerIds = previousReviewerIds.filter(function(tail) {
        return currentAssignedTails.indexOf(tail) < 0;
      });
      var availableSlots = Math.max(0, AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments - currentAssignedTails.length);
      $.when(
        getProfilesById(previousReviewerIds),
        getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersConflictId, AUTO_ASSIGN_CONFIG.noteId, previousReviewerIds),
        getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersPendingReviewsId, null, previousReviewerIds),
        getEdgesByTail(AUTO_ASSIGN_CONFIG.reviewersCustomMaxPapersId, null, previousReviewerIds),
        getReviewerStatsByTail(previousReviewerIds),
        loadPreviousReviewerMetadata(previousSubmission, previousReviewerIds)
      ).then(function(profilesById, conflictsByTail, pendingByTail, maxPapersByTail, statsByTail, previousMetadataByTail) {
        conflictsByTail = conflictsByTail || {};
        pendingByTail = pendingByTail || {};
        maxPapersByTail = maxPapersByTail || {};
        statsByTail = statsByTail || {};
        previousMetadataByTail = previousMetadataByTail || {};
        var authorRecommendationText = String(AUTO_ASSIGN_CONFIG.submissionCoverLetter || '').trim();
        var reviewerModels = previousReviewerIds.map(function(tail, index) {
          var profile = profilesById[tail] || null;
          var alreadyAssigned = currentAssignedTails.indexOf(tail) >= 0;
          var name = getProfileName(profile, tail);
          var continuityLabel = reviewerContinuityLabelForTail(tail, name);
          var previousMetadata = previousMetadataByTail[tail] || {};
          var email = getProfileEmails(profile, tail);
          var activePaperLoad = getEdgeWeight((pendingByTail[tail] || [])[0], 0);
          var maxPapers = getEdgeWeight((maxPapersByTail[tail] || [])[0], AUTO_ASSIGN_CONFIG.reviewersMaxPapers);
          var conflictEdge = (conflictsByTail[tail] || [])[0] || null;
          var availability = getPaperScopedReviewerAvailability(tail);
          var available = availability.state === 'available';
          var classification = classifyReviewerCandidate({
            tail: tail,
            name: name,
            continuityLabel: continuityLabel,
            email: email,
            affiliation: getProfileAffiliation(profile) || '',
            assigned: alreadyAssigned,
            conflictEdge: conflictEdge,
            availability: availability,
            availabilityAvailable: available,
            activePaperLoad: activePaperLoad,
            maxPapers: maxPapers
          });
          var openReviewConflict = classification && classification.severity === 'warning_conflict';
          var authorConflict = classification && classification.severity === 'author_conflict';
          return {
            tail: tail,
            name: name,
            email: email,
            affiliation: getProfileAffiliation(profile) || '',
            alreadyAssigned: alreadyAssigned,
            conflicted: openReviewConflict || authorConflict,
            openReviewConflict: openReviewConflict,
            authorConflict: authorConflict,
            classification: classification,
            continuityNumber: previousMetadata.continuityNumber || previousReviewerContinuityNumberForTail(tail) || ('Reviewer ' + (index + 1)),
            previousRecommendation: previousMetadata.previousRecommendation || 'No recommendation recorded',
            activePaperLoad: activePaperLoad,
            maxPapers: maxPapers,
            available: available,
            stats: statsByTail[tail]
          };
        });
        var rows = reviewerModels.map(function(model, index) {
          var assignable = assignableReviewerIds.indexOf(model.tail) >= 0;
          var checked = assignable && selectedPreviousReviewerIds.indexOf(model.tail) >= 0 && !model.conflicted ? ' checked' : '';
          var disabled = !assignable || model.conflicted || !availableSlots ? ' disabled' : '';
          var profileUrl = '/profile?id=' + encodeURIComponent(model.tail);
          return '<tr>' +
            '<td><input type="checkbox" class="previous-reviewer-candidate" value="' + escapeAutoAssignHtml(model.tail) + '"' + checked + disabled + '></td>' +
            '<td>' + escapeAutoAssignHtml(model.continuityNumber) + '</td>' +
            '<td style="width: 260px; min-width: 260px; max-width: 260px; white-space: normal; overflow-wrap: anywhere; word-break: break-word;"><strong>' + escapeAutoAssignHtml(model.continuityLabel) + '</strong><br><span class="text-muted">' + escapeAutoAssignHtml(model.name) + '</span><br><a class="text-muted" href="' + escapeAutoAssignHtml(profileUrl) + '" target="_blank" rel="noopener noreferrer">' + escapeAutoAssignHtml(model.tail) + '</a></td>' +
            '<td>' + escapeAutoAssignHtml(model.affiliation) + '</td>' +
            '<td>' + escapeAutoAssignHtml(model.previousRecommendation) + '</td>' +
            '<td>' + escapeAutoAssignHtml(model.activePaperLoad) + ' / ' + escapeAutoAssignHtml(model.maxPapers) + '</td>' +
            '<td>' + escapeAutoAssignHtml(reviewerStatsSummary(model.stats)) + '</td>' +
            '<td>' + formatReviewerConflictCell(model, model.alreadyAssigned ? 'Already assigned' : '') + '</td>' +
          '</tr>';
        }).join('');
        var nonConflictedAssignableReviewerIds = assignableReviewerIds.filter(function(tail) {
          var model = reviewerModels.find(function(item) { return item.tail === tail; }) || {};
          return !model.conflicted;
        });
        var hasConflictOverrideChoice = reviewerModels.some(function(model) {
          return model.openReviewConflict && assignableReviewerIds.indexOf(model.tail) >= 0;
        });
        var hasAuthorConflictChoice = reviewerModels.some(function(model) {
          return model.authorConflict && assignableReviewerIds.indexOf(model.tail) >= 0;
        });
        var hasLoadOrAvailabilityWarning = reviewerModels.some(function(model) {
          return !model.alreadyAssigned && assignableReviewerIds.indexOf(model.tail) >= 0 &&
            (!model.available || model.activePaperLoad >= model.maxPapers);
        });
        var warningSummary = [];
        if (hasConflictOverrideChoice) warningSummary.push('One or more previous reviewers have OpenReview conflict edges for this paper.');
        if (hasAuthorConflictChoice) warningSummary.push('One or more previous reviewers are listed as paper authors or author-declared conflicts and cannot be selected.');
        if (hasLoadOrAvailabilityWarning) warningSummary.push('One or more previous reviewers are unavailable or at/over configured active-review load; continuity assignment treats this as warning information.');
        var disabled = (!nonConflictedAssignableReviewerIds.length && !hasConflictOverrideChoice) || !availableSlots;
        var disabledReason = !assignableReviewerIds.length
          ? 'All previous reviewers are already assigned.'
          : (!availableSlots ? 'This paper already has the maximum number of reviewer assignments.' : '');
        $('#previous-reviewers-results').html(
          '<p class="text-muted">Previous paper: Paper ' + escapeAutoAssignHtml(previousSubmission.number) + '. Assignment is submitted through the normal reviewer assignment process, so backend eligibility checks and notifications still apply.</p>' +
          '<details style="margin-bottom: 10px;">' +
            '<summary><strong>Author reviewer recommendations and paper source</strong></summary>' +
            '<p style="margin-top: 8px;"><strong>Main paper PDF:</strong> <a href="' + escapeAutoAssignHtml(AUTO_ASSIGN_CONFIG.paperPdfUrl) + '" target="_blank" rel="noopener noreferrer">Open PDF</a></p>' +
            '<pre style="white-space: pre-wrap; margin: 8px 0 0; background: #f8f8f8; border: 1px solid #ddd; border-radius: 4px; padding: 8px;">' + escapeAutoAssignHtml(authorRecommendationText || 'No cover letter text was provided. If reviewer recommendations are only in the PDF, use the PDF link above.') + '</pre>' +
          '</details>' +
          '<div class="table-responsive" style="max-height: 360px; overflow-y: auto;">' +
            '<table class="table table-condensed table-striped">' +
              '<thead><tr><th style="width: 52px;">Select</th><th>Continuity #</th><th style="width: 260px; min-width: 260px; max-width: 260px;">Previous reviewer</th><th>Affiliation</th><th>Previous recommendation</th><th>Load</th><th>Rating / Timeliness</th><th>Status</th></tr></thead>' +
              '<tbody>' + rows + '</tbody>' +
            '</table>' +
          '</div>' +
          (warningSummary.length ? '<div class="alert alert-warning"><strong>Continuity warnings</strong><ul>' + warningSummary.map(function(item) { return '<li>' + escapeAutoAssignHtml(item) + '</li>'; }).join('') + '</ul></div>' : '') +
          (assignableReviewerIds.length ? '<div class="checkbox"><label><input id="include-conflicted-previous-reviewers" type="checkbox"> Include conflicted previous reviewers, and record a previous-reviewer conflict override for selected previous reviewers if OpenReview reports a conflict at submit time.</label></div>' : '') +
          (disabledReason ? '<p class="text-muted">' + escapeAutoAssignHtml(disabledReason) + '</p>' : '<p id="previous-reviewers-count-message" class="text-muted"></p>') +
          '<p>' + reviewerDueDateInputHtml('previous-reviewer-due-date') + '<button id="assign-previous-reviewers" type="button" class="btn btn-primary"' + (disabled ? ' disabled' : '') + '>Assign Previous Reviewers</button><span class="reviewer-assignment-button-status text-muted" style="margin-left: 8px;"></span></p>'
        );
        var getSelectedPreviousReviewerIds = function() {
          return $('.previous-reviewer-candidate:checked:not(:disabled)').map(function() { return $(this).val(); }).get();
        };
        var updatePreviousReviewerCountMessage = function() {
          var includeConflicted = $('#include-conflicted-previous-reviewers').prop('checked');
          $('.previous-reviewer-candidate').each(function() {
            var tail = $(this).val();
            var model = reviewerModels.find(function(item) { return item.tail === tail; }) || {};
            var assignable = assignableReviewerIds.indexOf(tail) >= 0;
            var shouldDisable = !assignable || !availableSlots || model.authorConflict || (model.openReviewConflict && !includeConflicted);
            $(this).prop('disabled', shouldDisable);
            if (shouldDisable) $(this).prop('checked', false);
          });
          var reviewerIdsToAssign = getSelectedPreviousReviewerIds();
          if (reviewerIdsToAssign.length > availableSlots) {
            reviewerIdsToAssign.slice(availableSlots).forEach(function(tail) {
              $('.previous-reviewer-candidate[value="' + tail.replace(/"/g, '\"') + '"]').prop('checked', false);
            });
            reviewerIdsToAssign = getSelectedPreviousReviewerIds();
          }
          $('#previous-reviewers-count-message').text('This will assign ' + reviewerIdsToAssign.length + ' previous reviewer(s), up to the configured maximum of ' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + ' total reviewers.');
          $('#assign-previous-reviewers').prop('disabled', !reviewerIdsToAssign.length);
        };
        $('#include-conflicted-previous-reviewers').off('change').on('change', updatePreviousReviewerCountMessage);
        $('.previous-reviewer-candidate').off('change').on('change', function() {
          var selectedReviewerIds = getSelectedPreviousReviewerIds();
          if (selectedReviewerIds.length > availableSlots) {
            $(this).prop('checked', false);
            setAutoAssignStatus('At most ' + AUTO_ASSIGN_CONFIG.maxTotalReviewerAssignments + ' reviewers can be assigned. Uncheck another reviewer first.', true);
          } else {
            setAutoAssignStatus('', false);
          }
          updatePreviousReviewerCountMessage();
        });
        updatePreviousReviewerCountMessage();
        $('#assign-previous-reviewers').off('click').on('click', function() {
          var button = $(this);
          var selectedDueDateMillis = reviewerDueDateMillisFromInput('previous-reviewer-due-date');
          if (isNaN(selectedDueDateMillis)) {
            setAutoAssignStatus('Review due date must use YYYY-MM-DD format.', true);
            return;
          }
          setReviewerAssignmentButtonBusy(button);
          var includeConflicted = $('#include-conflicted-previous-reviewers').prop('checked');
          var reviewerIdsToAssign = getSelectedPreviousReviewerIds();
          var attemptedAssignmentPayloads = reviewerIdsToAssign.map(function(tail) {
            return reviewerAssignmentEdgePayload(
              tail,
              signature,
              includeConflicted ? 'Previous Reviewer Conflict Override' : undefined
            );
          });
	  var assignmentChain = reviewerIdsToAssign.reduce(function(chain, tail) {
	    var assignmentIndex = reviewerIdsToAssign.indexOf(tail) + 1;
	    return chain.then(function() {
	      setReviewerAssignmentProgress(button, 'Submitting previous-reviewer assignment ' + assignmentIndex + ' of ' + reviewerIdsToAssign.length + '...', false);
	      return postCheckedReviewerAssignmentEdge(
	        tail,
	        signature,
                includeConflicted ? 'Previous Reviewer Conflict Override' : undefined,
                selectedDueDateMillis
              );
            });
	  }, Promise.resolve());
	  assignmentChain.then(function() {
            showReviewerAssignmentComplete(button, 'Assigned ' + reviewerIdsToAssign.length + ' previous reviewer(s).');
          }).catch(function(error) {
            error = error || {};
            if (typeof error !== 'object') error = { message: String(error) };
            if (!error.assignmentPayload && !error.assignmentPayloads) error.assignmentPayloads = attemptedAssignmentPayloads;
            var message = reviewerAssignmentErrorMessage(error, 'Unable to assign previous reviewers.');
            setReviewerAssignmentProgress(button, message, true);
            restoreReviewerAssignmentButton(button);
          });
        });
      });
    });
      }).fail(function(error) {
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || error || 'Unable to load previous reviewers.';
    $('#previous-reviewers-results').html('<p class="text-danger">' + escapeAutoAssignHtml(message) + '</p>');
      });
    }
"""
