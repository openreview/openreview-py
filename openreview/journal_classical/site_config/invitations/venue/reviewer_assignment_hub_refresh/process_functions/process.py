def process(client, edit, invitation):
    import datetime
    import json
    import re

    journal = openreview.journal.JournalRequest.get_journal(client, "{{PROD_JOURNAL_ID}}")
    trigger_note = client.get_note(edit.note.id)
    note_id = trigger_note.content.get('note_id', {}).get('value')
    if not note_id:
        raise openreview.OpenReviewException('Reviewer assignment hub refresh requires note_id.')
    note = client.get_note(note_id)
    expected_number = trigger_note.content.get('paper_number', {}).get('value')
    if expected_number and int(expected_number) != int(note.number):
        raise openreview.OpenReviewException('Reviewer assignment hub refresh paper_number does not match note_id.')

    invitation_refresh_namespace = {'openreview': openreview}
    exec("{{PYTHON_SCRIPT_JSON:invitations/venue/under_review/reviewer_assignment_invitation_refresh.py}}", invitation_refresh_namespace)
    reviewer_assignment_invitation = invitation_refresh_namespace['refresh_reviewer_assignment_invitation'](
        client,
        journal,
        note,
        journal.get_due_date(weeks=journal.get_reviewer_assignment_period_length())
    )

    web = reviewer_assignment_invitation.web or ''
    paper_reviewers_group_web = ''
    try:
        paper_reviewers_group = client.get_group(journal.get_reviewers_id(number=note.number))
        paper_reviewers_group_web = paper_reviewers_group.web or ''
    except Exception:
        paper_reviewers_group_web = ''
    if 'var AUTO_ASSIGN_CONFIG = ' not in web or 'var AUTO_ASSIGN_CONFIG = ' not in paper_reviewers_group_web:
        venue_group = client.get_group(journal.venue_id)
        venue_content = getattr(venue_group, 'content', {}) or {}
        hub_initializer_chunks = []
        missing_hub_initializer_chunks = []
        for chunk_index in range(1, 9):
            chunk_key = f'reviewer_assignment_hub_initializer_script_chunk_{chunk_index:02d}'
            chunk_value = (
                venue_content
                .get(chunk_key, {})
                .get('value')
            )
            if chunk_value is None:
                missing_hub_initializer_chunks.append(chunk_key)
            else:
                hub_initializer_chunks.append(chunk_value)
        if missing_hub_initializer_chunks:
            raise openreview.OpenReviewException(
                f"Reviewer assignment hub initializer script chunks are missing from {journal.venue_id}.content: "
                f"{', '.join(missing_hub_initializer_chunks)}."
            )
        hub_initializer_script = ''.join(hub_initializer_chunks)
        hub_namespace = {'openreview': openreview}
        exec(hub_initializer_script, hub_namespace)
        required_reviewers_namespace = {'openreview': openreview}
        exec("{{PYTHON_SCRIPT_JSON:invitations/venue/review/required_reviewers.py}}", required_reviewers_namespace)
        hub_namespace['refresh_reviewer_assignment_hub'](
            client,
            journal,
            note,
            journal.get_due_date(weeks=journal.get_reviewer_assignment_period_length()),
            required_reviewers_namespace['get_required_reviewers'](client, journal, note),
            journal.get_reviewers_max_papers(),
            json,
            __import__('html'),
            re,
        )
    else:
        def previous_submission_id_from_note(submission):
            previous_url = submission.content.get('previous_JMLR_submission_URL', {}).get('value') or ''
            match = re.search(r'forum\?id=([A-Za-z0-9_-]+)', str(previous_url))
            if match:
                return match.group(1)
            previous_list = submission.content.get('previous_JMLR_submissions', {}).get('value') or ''
            match = re.search(r'forum\?id=([A-Za-z0-9_-]+)', str(previous_list))
            return match.group(1) if match else ''

        def previous_submission_number_from_note(submission):
            previous_number = str(submission.content.get('previous_JMLR_submission_number', {}).get('value') or '').strip()
            if previous_number and previous_number.upper() != 'N/A':
                return previous_number
            previous_list = submission.content.get('previous_JMLR_submissions', {}).get('value') or ''
            match = re.search(r'Paper\s+([0-9]+)', str(previous_list))
            return match.group(1) if match else ''

        reviewer_candidate_tails = []
        try:
            reviewer_group = client.get_group(journal.get_reviewers_id())
            reviewer_candidate_tails = [
                member for member in (reviewer_group.members or [])
                if isinstance(member, str) and member.startswith('~')
            ]
        except Exception:
            reviewer_candidate_tails = []
        assigned_action_editor_signature = ''
        try:
            assigned_action_editor_signature = (client.get_group(journal.get_action_editors_id(number=note.number)).members or [''])[0]
        except Exception:
            assigned_action_editor_signature = ''

        now_millis = int(__import__('time').time() * 1000)
        reviewer_assignment_availability = {}
        try:
            reviewer_availability_edges = client.get_all_edges(invitation=journal.get_reviewer_availability_id())
        except Exception:
            reviewer_availability_edges = client.get_edges(invitation=journal.get_reviewer_availability_id())
        for availability_edge in reviewer_availability_edges or []:
            if (
                getattr(availability_edge, 'tail', None)
                and getattr(availability_edge, 'label', None) == 'Unavailable'
                and (
                    not getattr(availability_edge, 'weight', None)
                    or int(getattr(availability_edge, 'weight', 0)) > now_millis
                )
            ):
                reviewer_assignment_availability[availability_edge.tail] = {
                    'unavailableForAssignment': True
                }

        config_marker = 'var AUTO_ASSIGN_CONFIG = '
        config_start = web.find(config_marker)
        config_value_start = config_start + len(config_marker)
        auto_assign_config, auto_assign_config_length = json.JSONDecoder().raw_decode(web[config_value_start:])
        reviewer_assignment_id = journal.get_reviewer_assignment_id(number=note.number)
        reviewer_invite_assignment_id = journal.get_reviewer_invite_assignment_id()
        reviewer_assignment_hub_url = f'/group?id={journal.get_reviewers_id(number=note.number)}'
        reviewers_id = journal.get_reviewers_id()
        auto_assign_config['reviewerAssignmentAvailability'] = reviewer_assignment_availability
        auto_assign_config['reviewerCandidateTails'] = reviewer_candidate_tails
        auto_assign_config['assignmentBrowserContract'] = {
            'paper_id': note.id,
            'paper_number': note.number,
            'assignment_invitation': reviewer_assignment_id,
            'deployed_assignment_sources': [
                reviewer_assignment_id
            ],
            'readback_assignment_sources': [
                reviewer_assignment_id,
                reviewer_invite_assignment_id,
                f'{journal.venue_id}/Reviewers/-/Review_Due_Date'
            ],
            'score_sources': {
                'affinity_score_invitation': journal.get_reviewer_affinity_score_id(),
                'matching_input_group': f'{journal.venue_id}/Paper{note.number}/Reviewer_Matching_Input',
                'reviewer_stats_source': f'{journal.venue_id}/-/Submission'
            },
            'conflict_sources': {
                'openreview_conflict_invitation': journal.get_reviewer_conflict_id(),
                'candidate_refresh_invitation': f'{journal.venue_id}/-/Assignment_Candidate_Conflict_Refresh',
                'hard_author_fields': ['authorids', 'author_list', 'conflict_of_interests']
            },
            'availability_sources': {
                'reviewer_availability_invitation': journal.get_reviewer_availability_id(),
                'paper_scoped_config_key': 'reviewerAssignmentAvailability'
            },
            'load_sources': {
                'pending_reviews_invitation': journal.get_reviewer_pending_review_id(),
                'custom_max_papers_invitation': reviewers_id + '/-/Custom_Max_Papers',
                'assignment_history_sources': [
                    reviewer_assignment_id,
                    journal.get_reviewer_assignment_id()
                ]
            },
            'filter_semantics': {
                'candidate_group': reviewers_id,
                'requires_current_reviewer_membership': True,
                'blocks_hard_author_conflicts': True,
                'openreview_conflicts_are_override_warnings': True,
                'blocks_unavailable_reviewers': True,
                'checks_active_load_and_cooldown': True,
                'excludes_current_reviewers_from_new_assignment': True,
                'max_total_reviewer_assignments': 5
            },
            'allowed_signatures': [
                journal.get_editors_in_chief_id(),
                journal.get_action_editors_id(number=note.number)
            ],
            'legacy_read_only_sources': [
                journal.get_reviewer_assignment_id()
            ],
            'ui_boundary': {
                'visible_default_route': reviewer_assignment_hub_url,
                'raw_edges_browse_default': False
            }
        }
        auto_assign_config['reviewersAssignmentId'] = reviewer_assignment_id
        auto_assign_config['reviewersInviteAssignmentId'] = reviewer_invite_assignment_id
        auto_assign_config['assignedActionEditorSignature'] = assigned_action_editor_signature
        auto_assign_config['previousSubmissionId'] = previous_submission_id_from_note(note)
        auto_assign_config['previousSubmissionNumber'] = previous_submission_number_from_note(note)
        auto_assign_config['previousSubmissionList'] = note.content.get('previous_JMLR_submissions', {}).get('value') or ''
        auto_assign_config.pop('reviewersAvailabilityId', None)
        web = web[:config_value_start] + json.dumps(auto_assign_config) + web[config_value_start + auto_assign_config_length:]
        web = web.replace(
            "    if (!groups.length) {\n"
            "      return $.Deferred().reject('Could not find your anonymous action editor group for paper ' + AUTO_ASSIGN_CONFIG.paperNumber + '.').promise();\n"
            "    }\n",
            "    if (!groups.length) {\n"
            "      if (AUTO_ASSIGN_CONFIG.assignedActionEditorSignature) {\n"
            "        return AUTO_ASSIGN_CONFIG.assignedActionEditorSignature;\n"
            "      }\n"
            "      return $.Deferred().reject('Could not find your anonymous action editor group for paper ' + AUTO_ASSIGN_CONFIG.paperNumber + '.').promise();\n"
            "    }\n",
        )
        checked_assignment_helpers = """    function reviewerAssignmentBrowserContract() {
      return AUTO_ASSIGN_CONFIG.assignmentBrowserContract || {};
    }

    function reviewerAssignmentInvitationId() {
      return reviewerAssignmentBrowserContract().assignment_invitation || AUTO_ASSIGN_CONFIG.reviewersAssignmentId;
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

    function waitForReviewerAssignmentReadback(expectedTails, options) {
      expectedTails = _.uniq((expectedTails || []).filter(function(tail) { return !!tail; }));
      options = options || {};
      var maxAttempts = options.maxAttempts || 30;
      var delayMillis = options.delayMillis || 2000;
      var attempt = 0;
      var readOnce = function() {
    return $.when(
      Webfield2.api.getAll('/edges', {
        invitation: reviewerAssignmentInvitationId(),
        head: AUTO_ASSIGN_CONFIG.noteId,
        domain: AUTO_ASSIGN_CONFIG.venueId
      }),
      Webfield2.api.getGroup(getPaperReviewersGroupId(), { select: 'id,members' })
    ).then(function(edges, group) {
      var activeEdgeTails = _.uniq((edges || []).filter(function(edge) { return !edge.ddate; }).map(function(edge) { return edge.tail; }));
      var groupMembers = _.uniq((group && group.members || []).filter(function(member) { return !!member; }));
      var missingEdgeTails = expectedTails.filter(function(tail) { return activeEdgeTails.indexOf(tail) < 0; });
      var missingGroupTails = expectedTails.filter(function(tail) { return groupMembers.indexOf(tail) < 0; });
      return {
        ok: !missingEdgeTails.length && !missingGroupTails.length,
        missingEdgeTails: missingEdgeTails,
        missingGroupTails: missingGroupTails
      };
    });
      };
      var retry = function() {
    attempt += 1;
    return readOnce().then(function(readback) {
      if (readback.ok) return readback;
      if (options.onProgress) options.onProgress(attempt, maxAttempts, readback);
      if (attempt >= maxAttempts) {
        var missing = _.uniq(readback.missingEdgeTails.concat(readback.missingGroupTails));
        return $.Deferred().reject({
          message: 'Reviewer assignment submit completed, but checked assignment readback did not find assignment edge and paper reviewer group membership for: ' + missing.join(', ') + ' after ' + attempt + ' readback attempts.',
          readback: readback
        }).promise();
      }
      return new Promise(function(resolve, reject) {
        setTimeout(function() { retry().then(resolve, reject); }, delayMillis);
      });
    });
      };
      if (!expectedTails.length) return $.Deferred().resolve({ ok: true, activeEdgeTails: [], groupMembers: [] }).promise();
      return retry();
    }

    function reviewerAssignmentReadbackProgress(label) {
      return function(attempt, maxAttempts) {
    setAutoAssignStatus(label + ' Verifying reviewer assignment readback... attempt ' + attempt + '/' + maxAttempts + '.', false);
      };
    }

"""

        def upsert_checked_assignment_helpers(current_web):
            invite_marker = '    function setInviteEmailStatus(message, isError) {'
            helper_start = current_web.find('    function reviewerAssignmentOverrideLabel(candidate, actorSignature) {')
            invite_start = current_web.find(invite_marker)
            if invite_start < 0:
                raise openreview.OpenReviewException('Could not refresh reviewer assignment hub submit helpers: missing invite tab marker.')
            if helper_start >= 0 and helper_start < invite_start:
                return current_web[:helper_start] + checked_assignment_helpers + current_web[invite_start:]
            return current_web[:invite_start] + checked_assignment_helpers + current_web[invite_start:]

        def patch_manual_submit(current_web):
            current_web = current_web.replace(
                "    : null;\n      if (!until) return { blocked: false, until: 0 };",
                "    : null;\n      if (!until) {\n    var cooldownMillis = Number(AUTO_ASSIGN_CONFIG.reviewerNewAssignmentCooldownDays || 0) * 24 * 60 * 60 * 1000;\n    var now = Date.now();\n    var cutoff = now - cooldownMillis;\n    var latestRecentAssignment = (cooldownEdges || []).filter(function(edge) {\n      return edge && !edge.ddate && edge.head !== AUTO_ASSIGN_CONFIG.noteId && edge.cdate && edge.cdate >= cutoff;\n    }).sort(function(a, b) {\n      return Number(b.cdate || 0) - Number(a.cdate || 0);\n    })[0] || null;\n    until = latestRecentAssignment ? latestRecentAssignment.cdate + cooldownMillis : null;\n      }\n      if (!until) return { blocked: false, until: 0 };"
            )
            current_web = current_web.replace(
                "var severity = eligible ? 'eligible' : (openreviewConflict ? 'warning_conflict' : (unavailable ? 'unavailable' : 'blocked'));",
                "var severity = eligible ? 'eligible' : (unavailable ? 'unavailable' : (blockers.length ? 'blocked' : (openreviewConflict ? 'warning_conflict' : 'blocked')));"
            )
            current_web = current_web.replace(
                "quickLabel: eligible ? 'Looks eligible' : (openreviewConflict ? 'OpenReview conflict' : (unavailable ? 'Unavailable' : (blockers[0] && blockers[0].label || 'Not eligible'))),",
                "quickLabel: eligible ? 'Looks eligible' : (unavailable ? 'Unavailable' : (blockers[0] && blockers[0].label || (openreviewConflict ? 'OpenReview conflict' : 'Not eligible'))),"
            )
            current_web = current_web.replace(
                "selectable: true,\n      overridable: openreviewConflict,",
                "selectable: !unavailable && !blockers.length,\n      overridable: openreviewConflict && !unavailable && !blockers.length,"
            )
            current_web = re.sub(
                r"return Webfield2\.api\.post\('/edges', \{\s+invitation: AUTO_ASSIGN_CONFIG\.reviewersAssignmentId,\s+signatures: \[signature\],\s+head: AUTO_ASSIGN_CONFIG\.noteId,\s+tail: tail,\s+weight: 1,\s+label: selectedCandidate\.classification && selectedCandidate\.classification\.severity === 'warning_conflict' \? 'AE OpenReview Conflict Override' : undefined\s+\}\);",
                "return postCheckedReviewerAssignmentEdge(tail, signature, reviewerAssignmentOverrideLabel(selectedCandidate, signature), selectedDueDateMillis);",
                current_web,
            )
            current_web = re.sub(
                r"var message = error && error\.responseJSON && error\.responseJSON\.message;\n\s+if \(!message && error && error\.responseText\) \{\n\s+try \{\n\s+message = JSON\.parse\(error\.responseText\)\.message;\n\s+\} catch \(parseError\) \{\}\n\s+\}\n\s+message = message \|\| error && error\.message \|\| 'Unable to assign selected reviewers\.';",
                "var message = reviewerAssignmentErrorMessage(error, 'Unable to assign selected reviewers.');",
                current_web,
            )
            current_web = current_web.replace(
                "          if (!selectedTails.length) return;\n          button.prop('disabled', true).text('Completing...');\n          var handleAssignmentError = function(error) {",
                "          if (!selectedTails.length) return;\n          button.prop('disabled', true).text('Completing...');\n          var attemptedAssignmentPayloads = selectedTails.map(function(tail) {\n            var selectedCandidate = candidates.find(function(candidate) { return candidate.tail === tail; }) || {};\n            return reviewerAssignmentEdgePayload(tail, signature, reviewerAssignmentOverrideLabel(selectedCandidate, signature));\n          });\n          var handleAssignmentError = function(error) {"
            )
            current_web = current_web.replace(
                "          var handleAssignmentError = function(error) {\n            var message = reviewerAssignmentErrorMessage(error, 'Unable to assign selected reviewers.');",
                "          var handleAssignmentError = function(error) {\n            error = error || {};\n            if (typeof error !== 'object') error = { message: String(error) };\n            if (!error.assignmentPayload && !error.assignmentPayloads) error.assignmentPayloads = attemptedAssignmentPayloads;\n            var message = reviewerAssignmentErrorMessage(error, 'Unable to assign selected reviewers.');"
            )
            current_web = current_web.replace(
                "assignmentChain.then(function() {\n              setAutoAssignStatus('Assigned ' + newTails.length + ' reviewer(s). Reloading...', false);",
                "assignmentChain.then(function() {\n              setAutoAssignStatus('Assignment submitted. Verifying reviewer assignment readback...', false);\n              return waitForReviewerAssignmentReadback(newTails, {\n                onProgress: reviewerAssignmentReadbackProgress('Assignment submitted.')\n              });\n            }).then(function() {\n              setAutoAssignStatus('Assigned ' + newTails.length + ' reviewer(s). Reloading...', false);"
            )
            current_web = current_web.replace(
                "message = message || error && error.message || 'Unable to assign selected reviewers.';\n            setAutoAssignStatus(message + ' Refreshing current reviewer assignments...', true);",
                "message = message || error && error.message || 'Unable to assign selected reviewers.';\n            if (error && error.readback) {\n              setAutoAssignStatus(message, true);\n              button.prop('disabled', false).text('Assign Selected Reviewers');\n              return;\n            }\n            setAutoAssignStatus(message + ' Refreshing current reviewer assignments...', true);"
            )
            current_web = current_web.replace(
                "            var assignmentChain = newTails.reduce(function(chain, tail) {\n              return chain.then(function() {",
                "            if (!newTails.length) {\n              setAutoAssignStatus('The selected reviewers are already assigned. Reloading...', false);\n              reloadAutoAssignPage();\n              return;\n            }\n            var assignmentChain = newTails.reduce(function(chain, tail, index) {\n              return chain.then(function() {\n                setAutoAssignStatus('Submitting reviewer assignment ' + (index + 1) + ' of ' + newTails.length + '...', false);"
            )
            current_web = current_web.replace(
                "            setAutoAssignStatus(message + ' Refreshing current reviewer assignments...', true);\n            button.prop('disabled', false).text('Assign Selected Reviewers');\n            setTimeout(reloadAutoAssignPage, 2500);",
                "            setAutoAssignStatus(message, true);\n            button.prop('disabled', false).text('Assign Selected Reviewers');"
            )
            return current_web

        def patch_auto_submit(current_web):
            current_web = current_web.replace(
                "            var assignmentChain = selectedCandidates.reduce(function(chain, candidate) {\n              return chain.then(function() {",
                "            var assignmentChain = selectedCandidates.reduce(function(chain, candidate, index) {\n              return chain.then(function() {\n                setAutoAssignStatus('Submitting reviewer assignment ' + (index + 1) + ' of ' + selectedCandidates.length + '...', false);"
            )
            current_web = re.sub(
                r"return Webfield2\.api\.post\('/edges', \{\s+invitation: AUTO_ASSIGN_CONFIG\.reviewersAssignmentId,\s+signatures: \[signature\],\s+head: AUTO_ASSIGN_CONFIG\.noteId,\s+tail: candidate\.tail,\s+weight: 1,\s+label: candidate\.classification && candidate\.classification\.severity === 'warning_conflict' \? 'AE OpenReview Conflict Override' : undefined\s+\}\);",
                "return postCheckedReviewerAssignmentEdge(candidate.tail, signature, reviewerAssignmentOverrideLabel(candidate, signature), selectedDueDateMillis);",
                current_web,
            )
            current_web = re.sub(
                r"var message = error && error\.responseJSON && error\.responseJSON\.message;\n\s+if \(!message && error && error\.responseText\) \{\n\s+try \{\n\s+message = JSON\.parse\(error\.responseText\)\.message;\n\s+\} catch \(parseError\) \{\}\n\s+\}\n\s+message = message \|\| error && error\.message \|\| 'Unable to auto-assign reviewers\.';",
                "var message = reviewerAssignmentErrorMessage(error, 'Unable to auto-assign reviewers.');",
                current_web,
            )
            current_web = current_web.replace(
                "assignmentChain.then(function() {\n              setAutoAssignStatus('Assigned ' + selectedCandidates.length + ' reviewer(s). Reloading...', false);",
                "assignmentChain.then(function() {\n              setAutoAssignStatus('Assignment submitted. Verifying reviewer assignment readback...', false);\n              return waitForReviewerAssignmentReadback(selectedCandidates.map(function(candidate) { return candidate.tail; }), {\n                onProgress: reviewerAssignmentReadbackProgress('Assignment submitted.')\n              });\n            }).then(function() {\n              setAutoAssignStatus('Assigned ' + selectedCandidates.length + ' reviewer(s). Reloading...', false);"
            )
            current_web = current_web.replace(
                "message = message || error && error.message || 'Unable to auto-assign reviewers.';\n          setAutoAssignStatus(message + ' Refreshing current reviewer assignments...', true);",
                "message = message || error && error.message || 'Unable to auto-assign reviewers.';\n          if (error && error.readback) {\n            setAutoAssignStatus(message, true);\n            $('#confirm-auto-assign').prop('disabled', false).text('Assign Selected Reviewers');\n            return;\n          }\n          setAutoAssignStatus(message + ' Refreshing current reviewer assignments...', true);"
            )
            current_web = current_web.replace(
                "          setAutoAssignStatus(message + ' Refreshing current reviewer assignments...', true);\n          $('#confirm-auto-assign').prop('disabled', false).text('Assign Selected Reviewers');\n          setTimeout(reloadAutoAssignPage, 2500);",
                "          setAutoAssignStatus(message, true);\n          $('#confirm-auto-assign').prop('disabled', false).text('Assign Selected Reviewers');"
            )
            return current_web

        web = upsert_checked_assignment_helpers(web)
        web = patch_manual_submit(web)
        web = patch_auto_submit(web)
        if "postCheckedReviewerAssignmentEdge(tail, signature, reviewerAssignmentOverrideLabel(selectedCandidate, signature), selectedDueDateMillis)" not in web:
            raise openreview.OpenReviewException('Reviewer assignment hub refresh did not patch manual search submit path.')
        if "postCheckedReviewerAssignmentEdge(candidate.tail, signature, reviewerAssignmentOverrideLabel(candidate, signature), selectedDueDateMillis)" not in web:
            raise openreview.OpenReviewException('Reviewer assignment hub refresh did not patch auto-assign submit path.')

        reviewer_assignment_invitation.web = web
        paper_reviewers_group = client.get_group(journal.get_reviewers_id(number=note.number))
        paper_reviewers_group.readers = [
            journal.get_action_editors_id(note.number),
            journal.get_editors_in_chief_id()
        ]
        paper_reviewers_group.writers = list(dict.fromkeys(
            list(paper_reviewers_group.writers or []) + [
                journal.venue_id,
                journal.get_action_editors_id(note.number)
            ]
        ))
        paper_reviewers_group.web = web.replace('#invitation-container', '#group-container')
        client.post_group_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            readers=[journal.venue_id],
            writers=[journal.venue_id],
            group=paper_reviewers_group
        )
        client.post_invitation_edit(
            invitations=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            invitation=reviewer_assignment_invitation,
            replacement=True
        )

    try:
        client.post_note_edit(
            invitation=journal.get_meta_invitation_id(),
            signatures=[journal.venue_id],
            note=openreview.api.Note(
                id=trigger_note.id,
                ddate=openreview.tools.datetime_millis(datetime.datetime.now())
            )
        )
    except Exception as error:
        print(f'Could not expire reviewer assignment hub refresh trigger note {trigger_note.id}: {error}')
