INVITE_NEW_REVIEWERS_TAB_JS = r"""    function setInviteEmailStatus(message, isError) {
      $('#invite-new-reviewer-email-status')
    .text(message || '')
    .toggleClass('text-danger', !!isError)
    .toggleClass('alert alert-warning', !isError && !!message);
    }

    function setInviteEmailStatusHtml(html, isError) {
      $('#invite-new-reviewer-email-status')
    .html(html || '')
    .toggleClass('text-danger', !!isError)
    .toggleClass('alert alert-warning', !isError && !!html);
    }

    var REVIEWER_INVITE_LOOKUP_SEQUENCE = 0;
    var REVIEWER_INVITE_SEARCH_RESULT = null;

    function getReviewerInviteEmailPreview(email) {
      var recipient = email || '[reviewer email]';
      var pageLocation = typeof globalThis !== 'undefined' && globalThis.location ? globalThis.location : null;
      var siteOrigin = pageLocation && pageLocation.origin || '';
      var siteUrl = siteOrigin.charAt(siteOrigin.length - 1) === '/' ? siteOrigin.slice(0, -1) : siteOrigin;
      var subject = '[JMLR] Invitation to review paper titled "' + AUTO_ASSIGN_CONFIG.submissionTitle + '"';
      var reviewDueDate = $('#invite-reviewer-due-date').val() || defaultReviewerDueDateInputValue();
      var body = [
    'To: ' + recipient,
    '',
    'Hi {fullname},',
    '',
    'You have been invited to review the following JMLR submission:',
    '',
    'Paper ' + AUTO_ASSIGN_CONFIG.paperNumber + ': ' + AUTO_ASSIGN_CONFIG.submissionTitle,
    '',
    'Abstract:',
    AUTO_ASSIGN_CONFIG.submissionAbstract || '',
    '',
    'If you accept this invitation, please submit the review by ' + reviewDueDate + '.',
    '',
    'By accepting this invitation, you will also join the JMLR reviewer pool for potential future review requests, subject to active-assignment limits and your reviewer availability settings.',
    '',
    'Serving as a JMLR reviewer is an important service to the community. We aim to keep the reviewing duty reasonable: the number of active assignments is limited, and reviewers may adjust their reviewing load when needed, including setting their load to zero at any time.',
    '',
    'JMLR also recognizes outstanding reviewers. Reviewers with strong records, based on the number and quality of completed reviews, will be listed as the JMLR editorial board of reviewers on the JMLR website. This list is updated periodically. Reviewers may opt out of public Top Reviewer listing from the Reviewer Console without affecting review assignments.',
    '',
    'Accept:',
    '[OpenReview will generate a unique Accept link when the invite is sent.]',
    '',
    'Accepting this invitation requires signing in to OpenReview. If you already have an OpenReview account, please log in before opening the Accept link:',
    '',
    siteUrl + '/login',
    '',
    'If you do not yet have an OpenReview account, please create one, then log in and open the Accept link. OpenReview account sign-in is required to accept this invitation:',
    '',
    siteUrl + '/signup',
    '',
    'Decline:',
    '[OpenReview will generate a unique Decline link when the invite is sent.]',
    '',
    'If you are unable to review this submission, you may decline using the Decline link. Declining does not require OpenReview login.',
    '',
    'This invitation expires {INVITE_ASSIGNMENT_NO_RESPONSE_EXPIRATION_DAYS} days after it is sent if no response is recorded.',
    '',
    'Thank you for considering this review request.',
    '',
    'The JMLR Editors-in-Chief'
      ].join('\n');
      return { subject: subject, body: body };
    }

    function renderReviewerInviteEmailPreview(email) {
      var preview = getReviewerInviteEmailPreview(email);
      $('#invite-email-subject').text(preview.subject);
      $('#invite-email-body').val(preview.body);
      var pageDocument = typeof globalThis !== 'undefined' && globalThis.document ? globalThis.document : null;
      var subjectElement = pageDocument ? pageDocument.getElementById('invite-email-subject') : null;
      var bodyElement = pageDocument ? pageDocument.getElementById('invite-email-body') : null;
      if (subjectElement) subjectElement.textContent = preview.subject;
      if (bodyElement) {
    bodyElement.value = preview.body;
    bodyElement.textContent = preview.body;
      }
      return preview;
    }

    function updateReviewerInviteEmailPreview() {
      var email = ($('#invite-new-reviewer-email').val() || '').trim();
      renderReviewerInviteEmailPreview(email);
      REVIEWER_INVITE_SEARCH_RESULT = null;
      $('#send-reviewer-invite').hide().prop('disabled', true).text('Send Invite');
      setInviteEmailStatus('Search this email before sending so JMLR reviewer membership and known conflicts can be checked.', false);
    }

    function bindReviewerInviteEmailPreviewHandlers() {
      var pageDocument = typeof globalThis !== 'undefined' && globalThis.document ? globalThis.document : null;
      var emailElement = pageDocument ? pageDocument.getElementById('invite-new-reviewer-email') : null;
      var dueDateElement = pageDocument ? pageDocument.getElementById('invite-reviewer-due-date') : null;
      if (emailElement) {
    emailElement.oninput = updateReviewerInviteEmailPreview;
    emailElement.onchange = updateReviewerInviteEmailPreview;
    emailElement.onkeyup = updateReviewerInviteEmailPreview;
      }
      if (dueDateElement) {
    var updatePreviewForDate = function() {
      renderReviewerInviteEmailPreview(($('#invite-new-reviewer-email').val() || '').trim());
    };
    dueDateElement.oninput = updatePreviewForDate;
    dueDateElement.onchange = updatePreviewForDate;
      }
    }

    function getReviewerInviteProfileFromSearchResult(result, email) {
      if (!result) return null;
      if (result.profile && result.profile.id) return result.profile;
      var profiles = result.profiles || [];
      if (!Array.isArray(profiles)) {
    profiles = email && profiles[email] ? profiles[email] : Object.keys(profiles).map(function(key) { return profiles[key]; });
      }
      profiles = [].concat.apply([], profiles || []);
      for (var i = 0; i < profiles.length; i += 1) {
    var profile = profiles[i] && profiles[i].profile || profiles[i];
    if (profile && profile.id) return profile;
      }
      return null;
    }

    function reviewerInviteProfileSearch(requestFactory, email) {
      return requestFactory().then(function(result) {
    return getReviewerInviteProfileFromSearchResult(result, email);
      }, function() {
    return null;
      });
    }

    function getReviewerInviteProfileFromConfig(email) {
      var lookup = AUTO_ASSIGN_CONFIG.reviewerInviteProfileLookup || {};
      var key = String(email || '').trim().toLowerCase();
      return key && lookup[key] && lookup[key].id ? lookup[key] : null;
    }

    function getReviewerInviteProfileFromPreferredEmailEdge(email) {
      if (!email) return $.Deferred().resolve(null).promise();
      var preferredEmailsId = AUTO_ASSIGN_CONFIG.preferredEmailsId || (AUTO_ASSIGN_CONFIG.venueId + '/-/Preferred_Emails');
      return Webfield2.api.getAll('/edges', {
    invitation: preferredEmailsId,
    tail: email
      }).then(function(edges) {
    edges = (edges || []).filter(function(edge) {
      return edge && !edge.ddate && edge.head;
    });
    if (!edges.length) return null;
    return reviewerInviteProfileSearch(function() {
      return Webfield2.api.post('/profiles/search', { ids: [edges[0].head] });
    }, edges[0].head);
      }, function() {
    return null;
      });
    }

    function resolveReviewerInviteProfile(email) {
      if (!email) return $.Deferred().resolve(null).promise();
      var configProfile = getReviewerInviteProfileFromConfig(email);
      if (configProfile && configProfile.id) return $.Deferred().resolve(configProfile).promise();
      return getReviewerInviteProfileFromPreferredEmailEdge(email).then(function(edgeProfile) {
    if (edgeProfile && edgeProfile.id) return edgeProfile;
    return reviewerInviteProfileSearch(function() {
    return Webfield2.api.post('/profiles/search', { ids: [email] });
    }, email).then(function(profile) {
    if (profile && profile.id) return profile;
    return reviewerInviteProfileSearch(function() {
      return Webfield2.api.get('/profiles/search', { term: email, es: 'true' });
    }, email);
    });
      });
    }

    function getReviewerInviteConflictStatus(profile) {
      if (!profile || !profile.id) {
    return $.Deferred().resolve({
      severity: 'warning',
      label: 'No OpenReview profile was found for this email. Check known conflicts manually before sending this invitation.'
    }).promise();
      }
      var hardAuthorConflict = getReviewerAssignmentHardAuthorConflict(profile.id);
      if (hardAuthorConflict) {
    return $.Deferred().resolve({
      severity: 'error',
      label: hardAuthorConflict.label || 'Author conflict detected'
    }).promise();
      }
      var helperClassification = classifyReviewerCandidate({
    tail: profile.id,
    name: getProfileName(profile, profile.id),
    email: getProfileEmails(profile, ''),
    affiliation: getProfileAffiliation(profile),
    assigned: false,
    availabilityAvailable: true,
    activePaperLoad: 0,
    maxPapers: Infinity
      });
      if (helperClassification && helperClassification.severity === 'author_conflict') {
    return $.Deferred().resolve({
      severity: 'error',
      label: helperClassification.conflict && helperClassification.conflict.label || 'Author conflict detected'
    }).promise();
      }
      return getAutoAssignmentSignature().then(function(signature) {
    return materializeOnDemandReviewerConflict(profile.id, signature);
      }).then(function() {
    return Webfield2.api.getAll('/edges', {
      invitation: AUTO_ASSIGN_CONFIG.reviewersConflictId,
      head: AUTO_ASSIGN_CONFIG.noteId,
      tail: profile.id,
      domain: AUTO_ASSIGN_CONFIG.venueId
    });
      }, function() {
    return $.Deferred().reject({
      message: 'Unable to refresh OpenReview conflict edges. Check known conflicts manually before sending.'
    }).promise();
      }).then(function(edges) {
    var hasConflict = (edges || []).some(function(edge) {
      return !edge.ddate && (edge.weight === undefined || edge.weight === null || Number(edge.weight) !== 0);
    });
    return hasConflict
      ? { severity: 'warning', label: 'OpenReview reports a conflict for this reviewer. This is an AE/EIC warning, not a hard block for external invitations.' }
      : { severity: 'ok', label: 'No OpenReview conflict detected for this paper.' };
      }, function() {
    return { severity: 'warning', label: 'Unable to check OpenReview conflict edges. Check known conflicts manually before sending.' };
      });
    }

    function refreshReviewerInviteConflictStatusOnDemand(profile) {
      return getReviewerInviteConflictStatus(profile).then(function(conflictStatus) {
    return conflictStatus || {
      severity: 'warning',
      label: 'Unable to refresh OpenReview conflict status. Check known conflicts manually before sending.'
    };
      }, function() {
    return {
      severity: 'warning',
      label: 'Unable to refresh OpenReview conflict status. Check known conflicts manually before sending.'
    };
      });
    }

    function renderReviewerInviteProfileStatus(email, profile, isReviewer, conflictStatus) {
      if (!profile || !profile.id) {
    return '<strong>Profile status:</strong> No OpenReview profile found for ' + escapeAutoAssignHtml(email) + '.<br>' +
      '<span class="text-warning">Check known conflicts manually before sending this invitation.</span>';
      }
      var conflictClass = conflictStatus && conflictStatus.severity === 'error'
    ? 'text-danger'
    : (conflictStatus && conflictStatus.severity === 'warning' ? 'text-warning' : 'text-muted');
      var rows = [
    ['OpenReview ID', '<a href="/profile?id=' + encodeURIComponent(profile.id) + '" target="_blank" rel="noopener noreferrer">' + escapeAutoAssignHtml(profile.id) + '</a>'],
    ['Name', getProfileName(profile, profile.id)],
    ['Affiliation', getProfileAffiliation(profile) || 'Not listed'],
    ['Conflict status', conflictStatus && conflictStatus.label || 'Not checked']
      ];
      var details = '<strong>Profile status:</strong>' +
    '<dl class="dl-horizontal" style="margin-top: 8px; margin-bottom: 0;">' +
      rows.map(function(row) {
        var value = row[0] === 'OpenReview ID' ? row[1] : escapeAutoAssignHtml(row[1]);
        return '<dt>' + escapeAutoAssignHtml(row[0]) + '</dt><dd class="' + (row[0] === 'Conflict status' ? conflictClass : '') + '">' + value + '</dd>';
      }).join('') +
    '</dl>';
      if (isReviewer) {
    return details +
      '<div class="text-danger" style="margin-top: 8px;"><strong>This OpenReview profile is already a JMLR reviewer.</strong> Use Search Reviewers to assign them instead of sending an external invitation.</div>';
      }
      return details;
    }

    function reviewerInviteResultAllowsSend(result) {
      if (!result) return false;
      if (result.isReviewer) return false;
      return !(result.conflictStatus && result.conflictStatus.severity === 'error');
    }

    function lookupReviewerInviteEmail(email) {
      if (!email) return $.Deferred().resolve({ profile: null, isReviewer: false, conflictStatus: null }).promise();
      return resolveReviewerInviteProfile(email).then(function(profile) {
    if (!profile || !profile.id) {
      return { profile: null, isReviewer: false, conflictStatus: {
        severity: 'warning',
        label: 'No OpenReview profile was found for this email. Check known conflicts manually before sending this invitation.'
      } };
    }
    return $.when(isCurrentJMLRReviewer(profile.id), refreshReviewerInviteConflictStatusOnDemand(profile)).then(function(isReviewer, conflictStatus) {
      return { profile: profile, isReviewer: isReviewer, conflictStatus: conflictStatus };
    });
      });
    }

    function searchReviewerInviteEmail() {
      var email = getEmailInviteAddress();
      if (!email) {
    REVIEWER_INVITE_SEARCH_RESULT = null;
    $('#send-reviewer-invite').hide().prop('disabled', true).text('Send Invite');
    return;
      }
      renderReviewerInviteEmailPreview(email);
      REVIEWER_INVITE_LOOKUP_SEQUENCE += 1;
      var lookupSequence = REVIEWER_INVITE_LOOKUP_SEQUENCE;
      REVIEWER_INVITE_SEARCH_RESULT = null;
      $('#search-reviewer-invite').prop('disabled', true).text('Searching...');
      $('#send-reviewer-invite').hide().prop('disabled', true).text('Send Invite');
      setInviteEmailStatus('Checking OpenReview profile and conflict status for ' + email + '.', false);
      lookupReviewerInviteEmail(email).then(function(result) {
    if (lookupSequence !== REVIEWER_INVITE_LOOKUP_SEQUENCE) return;
    result = result || {};
    result.email = email;
    REVIEWER_INVITE_SEARCH_RESULT = result;
    setInviteEmailStatusHtml(
      renderReviewerInviteProfileStatus(email, result.profile, result.isReviewer, result.conflictStatus),
      !!result.isReviewer || !!(result.conflictStatus && result.conflictStatus.severity === 'error')
    );
    if (reviewerInviteResultAllowsSend(result)) {
      $('#send-reviewer-invite').show().prop('disabled', false).text('Send Invite');
    }
      }, function() {
    if (lookupSequence !== REVIEWER_INVITE_LOOKUP_SEQUENCE) return;
    REVIEWER_INVITE_SEARCH_RESULT = null;
    setInviteEmailStatus('Unable to check OpenReview profile or conflicts. Check known conflicts manually before sending.', false);
      }).always(function() {
    if (lookupSequence !== REVIEWER_INVITE_LOOKUP_SEQUENCE) return;
    $('#search-reviewer-invite').prop('disabled', false).text('Search');
      });
    }

    function isCurrentJMLRReviewer(profileId) {
      if (!profileId) return $.Deferred().resolve(false).promise();
      return Webfield2.api.get('/groups', {
    id: AUTO_ASSIGN_CONFIG.reviewersId,
    member: profileId,
    limit: 1
      }).then(function(result) {
    var groups = result && result.groups || [];
    return groups.some(function(group) { return group && group.id === AUTO_ASSIGN_CONFIG.reviewersId; });
      }, function() {
    return false;
      });
    }

    function checkReviewerInviteConflict(email) {
      return lookupReviewerInviteEmail(email).then(function(result) {
    result = result || {};
    if (!result.profile || !result.profile.id) {
      return {
        blocked: false,
        profile: null,
        warning: 'No OpenReview profile was found for this email. Check known conflicts manually before sending this invitation.'
      };
    }
    if (result.isReviewer) {
      return {
        blocked: true,
        profile: result.profile,
        reason: 'This person is already a current JMLR reviewer. Use Search Reviewers to assign them instead of sending an external invitation.'
      };
    }
    if (result.conflictStatus && result.conflictStatus.severity === 'error') {
      return {
        blocked: true,
        profile: result.profile,
        reason: 'This reviewer is listed as a paper author or author-declared conflict and cannot be invited.'
      };
    }
    if (result.conflictStatus && result.conflictStatus.severity === 'warning') {
      return {
        blocked: false,
        profile: result.profile,
        warning: result.conflictStatus.label
      };
    }
    return { blocked: false, profile: result.profile };
      });
    }

    function getEmailInviteAddress() {
      var email = ($('#invite-new-reviewer-email').val() || '').trim();
      if (!email) {
    setAutoAssignStatus('Enter the reviewer email address to invite.', true);
    setInviteEmailStatus('No email entered.', true);
    return null;
      }
      email = email.trim();
      var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(email)) {
    setAutoAssignStatus('Please enter a valid email address.', true);
    setInviteEmailStatus('Invalid email: ' + email, true);
    return null;
      }
      return email;
    }

    function getAutoAssignmentSignature() {
      var profileId = user && user.profile && user.profile.id || user && user.id;
      if (!profileId) return $.Deferred().reject('Could not determine your OpenReview profile signature.').promise();
      return Webfield2.api.get('/groups', {
    prefix: AUTO_ASSIGN_CONFIG.venueId + '/' + AUTO_ASSIGN_CONFIG.submissionGroupName + AUTO_ASSIGN_CONFIG.paperNumber + '/Action_Editor_',
    signatory: profileId
      }).then(function(result) {
    var groups = result.groups || [];
    if (!groups.length) {
      if (AUTO_ASSIGN_CONFIG.assignedActionEditorSignature) {
        return AUTO_ASSIGN_CONFIG.assignedActionEditorSignature;
      }
      return $.Deferred().reject('Could not find your anonymous action editor group for paper ' + AUTO_ASSIGN_CONFIG.paperNumber + '.').promise();
    }
    return groups[0].id;
      });
    }

    function submitReviewerEmailInvite() {
      var email = getEmailInviteAddress();
      if (!email) return;
      renderReviewerInviteEmailPreview(email);
      if (!REVIEWER_INVITE_SEARCH_RESULT || REVIEWER_INVITE_SEARCH_RESULT.email !== email) {
    setAutoAssignStatus('Search this email before sending the invitation.', true);
    setInviteEmailStatus('Search this email before sending so JMLR reviewer membership and known conflicts can be checked.', true);
    $('#send-reviewer-invite').hide().prop('disabled', true).text('Send Invite');
    return;
      }
      if (!reviewerInviteResultAllowsSend(REVIEWER_INVITE_SEARCH_RESULT)) {
    var reason = REVIEWER_INVITE_SEARCH_RESULT.isReviewer
      ? 'This person is already a current JMLR reviewer. Use Search Reviewers to assign them instead of sending an external invitation.'
      : 'This reviewer is listed as a paper author or author-declared conflict and cannot be invited.';
    setAutoAssignStatus(reason, true);
    setInviteEmailStatus(reason, true);
    $('#send-reviewer-invite').hide().prop('disabled', true).text('Send Invite');
    return;
      }
      var selectedDueDateMillis = reviewerDueDateMillisFromInput('invite-reviewer-due-date');
      if (isNaN(selectedDueDateMillis)) {
    setAutoAssignStatus('Review due date must use YYYY-MM-DD format.', true);
    setInviteEmailStatus('Review due date must use YYYY-MM-DD format.', true);
    return;
      }
      setInviteEmailStatus('Sending invitation to ' + email + '.', false);
      $('#send-reviewer-invite').prop('disabled', true).text('Inviting...');
      $.when(getAutoAssignmentSignature(), checkReviewerInviteConflict(email)).then(function(signature, conflictCheck) {
    conflictCheck = conflictCheck || { blocked: false };
    if (conflictCheck.blocked) {
      setAutoAssignStatus(conflictCheck.reason, true);
      setInviteEmailStatus(conflictCheck.reason, true);
      $('#send-reviewer-invite').prop('disabled', false).text('Send Invite');
      return $.Deferred().reject({ handled: true }).promise();
    }
    if (conflictCheck.warning) {
      setAutoAssignStatus(conflictCheck.warning, false);
      setInviteEmailStatus(conflictCheck.warning, false);
    }
    var inviteEmailTail = email;
    return Webfield2.api.post('/edges', {
      invitation: AUTO_ASSIGN_CONFIG.reviewersInviteAssignmentId,
      signatures: [signature],
      head: AUTO_ASSIGN_CONFIG.noteId,
      tail: inviteEmailTail,
      weight: selectedDueDateMillis,
      ddate: Date.now() + Number(AUTO_ASSIGN_CONFIG.inviteAssignmentNoResponseExpirationDays || 21) * 24 * 60 * 60 * 1000,
      label: 'Invitation Sent'
    });
      }).then(function() {
    setAutoAssignStatus('Invited ' + email + '. Refresh the page to see current reviewer invitations.', false);
    setInviteEmailStatus('Invited ' + email + '. Refresh the page to see current reviewer invitations.', false);
    $('#send-reviewer-invite').prop('disabled', false).text('Send Invite');
      }, function(error) {
    if (error && error.handled) return;
    var message = error && error.responseJSON && error.responseJSON.message || error && error.message || 'Unable to invite reviewer.';
    setAutoAssignStatus(message, true);
    setInviteEmailStatus('Could not invite ' + email + '.', true);
    $('#send-reviewer-invite').prop('disabled', false).text('Send Invite');
      });
    }

    function showReviewerInviteForm() {
      $('#confirm-auto-assign-container').remove();
      $('#auto-assign-reviewers').prop('disabled', false).text('Auto-assign Reviewers');
      hideReviewerSearchPanel();
      $('#invite-new-reviewer-container').show();
      bindReviewerInviteEmailPreviewHandlers();
      $('#invite-new-reviewer-email').focus();
      setAutoAssignStatus('Enter the email address of the reviewer to invite.', false);
      updateReviewerInviteEmailPreview();
      setTimeout(updateReviewerInviteEmailPreview, 0);
      setTimeout(updateReviewerInviteEmailPreview, 100);
    }

    function hideReviewerInviteForm() {
      $('#invite-new-reviewer-container').hide();
      $('#invite-new-reviewer-email').val('');
      REVIEWER_INVITE_SEARCH_RESULT = null;
      $('#send-reviewer-invite').hide().prop('disabled', true).text('Send Invite');
      $('#search-reviewer-invite').prop('disabled', false).text('Search');
      setInviteEmailStatus('', false);
      setAutoAssignStatus('', false);
    }
"""
