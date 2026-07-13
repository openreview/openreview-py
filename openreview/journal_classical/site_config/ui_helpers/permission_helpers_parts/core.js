/*
 * Shared UI permission helper models for JMLR OpenReview webfields.
 *
 * These helpers intentionally cover permission-sensitive decisions only.
 * Webfields may own layout and presentation, but should render these models
 * instead of recomputing role, action, signature, or debug visibility rules.
 */

;(function(root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory()
  } else {
    root.JMLRPermissionHelpers = factory()
  }
})(typeof self !== 'undefined' ? self : this, function() {
  var ROLE_AUTHOR = 'author'
  var ROLE_REVIEWER = 'reviewer'
  var ROLE_AE = 'ae'
  var ROLE_EIC = 'eic'
  var ROLE_PE = 'pe'
  var ROLE_READ_ONLY = 'read-only'
  var ROLE_NONE = 'none'
  var DEBUG_ENVS = { dev: true, test: true, local: true }

  function asList(value) {
    if (!value) return []
    return Array.isArray(value) ? value : [value]
  }

  function escapeHtml(value) {
    if (typeof _ !== 'undefined' && _.escape) return _.escape(value)
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;')
  }

  function renderPreviousSubmissionsList(value, fallbackNumber, fallbackUrl) {
    var rows = []
    String(value || '').split('\n').forEach(function(line) {
      var match = line.match(/\[Paper\s+([^\]]+)\]\(([^)]+)\)/)
      if (match) rows.push({ number: match[1], url: match[2] })
    })
    if (!rows.length && fallbackUrl && fallbackUrl.toUpperCase() !== 'N/A') {
      rows.push({
        number: fallbackNumber && fallbackNumber.toUpperCase() !== 'N/A' ? fallbackNumber : 'previous round',
        url: fallbackUrl
      })
    }
    if (!rows.length) return ''
    return '<ul style="margin: 4px 0 6px 18px; padding-left: 0;">' + rows.map(function(row) {
      var label = row.number === 'previous round' ? 'previous round' : 'Paper ' + row.number
      return '<li><a href="' + escapeHtml(row.url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(label) + '</a></li>'
    }).join('') + '</ul>'
  }

  function getPublicationLifecycleLabel(venueId, venuePrefix) {
    venuePrefix = venuePrefix || 'JMLR'
    var value = String(venueId || '')
    if (value === venuePrefix + '/Camera_Ready_Published') return 'Published'
    if (value === venuePrefix + '/Publication_Retracted') return 'Publication retracted'
    if (value === venuePrefix + '/Camera_Ready_Approved') return 'Camera ready approved'
    if (value === venuePrefix + '/Camera_Ready_Check_Pending') return 'Camera-ready check pending'
    if (value === venuePrefix + '/Camera_Ready_Revision_Pending') return 'Camera-ready revision requested'
    return ''
  }

  function isPublishedPublicationLifecycle(venueId, venuePrefix) {
    venuePrefix = venuePrefix || 'JMLR'
    return venueId === venuePrefix + '/Camera_Ready_Published' ||
      venueId === venuePrefix + '/Publication_Retracted'
  }

  function unique(values) {
    var seen = {}
    return values.filter(function(value) {
      if (value === null || value === undefined || seen[value]) return false
      seen[value] = true
      return true
    })
  }

  function envelope(config) {
    config = config || {}
    return {
      ok: config.ok !== false,
      context: config.context || {},
      model: config.model || {},
      items: config.items || [],
      hidden_items: config.hidden_items || [],
      debug_items: config.debug_items || [],
      reasons: config.reasons || [],
      meta: config.meta || {}
    }
  }

  function makeRenderItem(type, id, config) {
    config = config || {}
    var item = {
      type: type,
      id: id,
      label: config.label || String(id || '').split('/').pop().replace(/_/g, ' '),
      visible: config.visible !== false,
      enabled: config.enabled !== false,
      role_context: config.role_context || null,
      source: config.source || {},
      data: config.data || {},
      reasons: config.reasons || []
    }
    if (config.debug_visible) item.debug_visible = true
    return item
  }

  function normalizeActor(user, memberships) {
    user = user || {}
    var profile = user.profile || user
    var profileId = profile.id || user.id
    var emails = asList(profile.emails).concat(asList(user.emails))
    return {
      profile_id: profileId,
      ids: unique([profileId, user.id].concat(asList(user.ids), emails)),
      emails: unique(emails),
      memberships: unique(asList(memberships).concat(asList(user.memberships)))
    }
  }

  function groupMembers(group) {
    return asList(group && group.members)
  }

  function isGroupMember(actorContext, groupId, groupCache) {
    groupCache = groupCache || {}
    if (!groupId) return { ok: false, reason: 'not_group_member' }
    if (actorContext.memberships && actorContext.memberships.indexOf(groupId) >= 0) {
      return { ok: true, reason: 'actor_membership' }
    }
    if (actorContext.ids && actorContext.ids.indexOf(groupId) >= 0) {
      return { ok: true, reason: 'actor_id_matches_group' }
    }
    var members = groupMembers(groupCache[groupId])
    var ok = (actorContext.ids || []).some(function(id) { return members.indexOf(id) >= 0 })
    return ok ? { ok: true, reason: 'group_member' } : { ok: false, reason: 'not_group_member' }
  }

  function matchesPrincipal(actorContext, principal, groupCache) {
    if (principal === 'everyone' || principal === 'Everyone') return true
    if ((actorContext.ids || []).indexOf(principal) >= 0) return true
    return isGroupMember(actorContext, principal, groupCache).ok
  }

  function matchesReaders(actorContext, readers, nonreaders, groupCache) {
    groupCache = groupCache || {}
    var blocked = asList(nonreaders).some(function(principal) {
      return matchesPrincipal(actorContext, principal, groupCache)
    })
    if (blocked) return { ok: false, reason: 'matched_nonreader' }
    var readerList = asList(readers)
    if (!readerList.length) return { ok: false, reason: 'no_readers' }
    var ok = readerList.some(function(principal) {
      return matchesPrincipal(actorContext, principal, groupCache)
    })
    return ok ? { ok: true, reason: 'matched_reader' } : { ok: false, reason: 'not_in_readers' }
  }

  function loadActorContext(user, config) {
    config = config || {}
    var actorContext = normalizeActor(user, config.memberships)
    return envelope({ context: { actor_id: actorContext.profile_id }, model: { actor_context: actorContext } })
  }

  function loadPaperContext(config) {
    config = config || {}
    var submission = config.submission || config.paper || {}
    var paperContext = {
      submission: submission,
      paper_id: submission.id || submission.forum,
      paper_number: submission.number,
      paper_state: submission.content && submission.content.venueid && (submission.content.venueid.value || submission.content.venueid) || 'unknown',
      invitations: config.invitations || [],
      notes: config.notes || [],
      details: config.details || [],
      groups: config.groups || {},
      edges: config.edges || [],
      desired_catalog: config.desired_catalog || {}
    }
    return envelope({ context: { paper_id: paperContext.paper_id, paper_number: paperContext.paper_number }, model: { paper_context: paperContext } })
  }

  function loadVenueContext(config) {
    config = config || {}
    var venueId = config.venue_id || 'JMLR'
    var venueContext = {
      venue_id: venueId,
      role_groups: config.role_groups || {
        author: venueId + '/Authors',
        reviewer: venueId + '/Reviewers',
        ae: venueId + '/Action_Editors',
        eic: venueId + '/Editors_In_Chief',
        pe: venueId + '/Production_Editors'
      },
      submissions: config.submissions || [],
      invitations: config.invitations || [],
      edges: config.edges || [],
      people: config.people || []
    }
    return envelope({ context: { venue_id: venueId }, model: { venue_context: venueContext } })
  }

  function entryPointRole(entryPoint) {
    var value = String(entryPoint || '').toLowerCase().replace(/-/g, '_')
    if (!value) return null
    if (value.indexOf('author') >= 0) return ROLE_AUTHOR
    if (value.indexOf('reviewer') >= 0) return ROLE_REVIEWER
    if (value.indexOf('action_editor') >= 0 || value.indexOf('ae_console') >= 0) return ROLE_AE
    if (value.indexOf('editor_in_chief') >= 0 || value.indexOf('eic') >= 0) return ROLE_EIC
    if (value.indexOf('production_editor') >= 0 || value.indexOf('pe_console') >= 0) return ROLE_PE
    return null
  }

  function paperGroupId(paperContext, suffix, venueId) {
    return (venueId || 'JMLR') + '/Paper' + paperContext.paper_number + '/' + suffix
  }

  function paperAuthorIds(paperContext) {
    var submission = paperContext && paperContext.submission || {}
    return asList(contentValue(submission.content || {}, 'authorids'))
  }

  function actorMatchesAny(actorContext, values) {
    var ids = actorContext && actorContext.ids || []
    return asList(values).some(function(value) {
      return ids.indexOf(value) >= 0
    })
  }

  function roleMembershipOk(roleContext, actorContext, paperContext, venueContext) {
    paperContext = paperContext || {}
    venueContext = venueContext || {}
    var groups = paperContext.groups || {}
    var venueId = venueContext.venue_id || 'JMLR'
    var roleGroups = venueContext.role_groups || {
      author: venueId + '/Authors',
      reviewer: venueId + '/Reviewers',
      ae: venueId + '/Action_Editors',
      eic: venueId + '/Editors_In_Chief',
      pe: venueId + '/Production_Editors'
    }
    if (roleContext === ROLE_AUTHOR) {
      return actorMatchesAny(actorContext, paperAuthorIds(paperContext)) ||
        isGroupMember(actorContext, paperGroupId(paperContext, 'Authors', venueId), groups).ok
    }
    if (roleContext === ROLE_REVIEWER) return isGroupMember(actorContext, paperGroupId(paperContext, 'Reviewers', venueId), groups).ok
    if (roleContext === ROLE_AE) return isGroupMember(actorContext, paperGroupId(paperContext, 'Action_Editors', venueId), groups).ok
    if (roleContext === ROLE_EIC || roleContext === ROLE_PE) return isGroupMember(actorContext, roleGroups[roleContext], groups).ok
    if (roleContext === ROLE_READ_ONLY) {
      return matchesReaders(actorContext, paperContext.submission && paperContext.submission.readers || ['everyone'], paperContext.submission && paperContext.submission.nonreaders || [], groups).ok
    }
    return false
  }

  function allowedContexts(actorContext, paperContext, venueContext) {
    return [ROLE_AUTHOR, ROLE_REVIEWER, ROLE_AE, ROLE_EIC, ROLE_PE, ROLE_READ_ONLY].filter(function(role) {
      return roleMembershipOk(role, actorContext, paperContext, venueContext)
    })
  }

  function resolveRoleContext(actorContext, paperContext, config) {
    config = config || {}
    var explicitRole = config.requested_role_context || entryPointRole(config.entry_point)
    var reasons = []
    var fallbackUsed = false
    var roleContext = ROLE_NONE
    if (explicitRole) {
      var isConflictedEicAuthor = explicitRole === ROLE_EIC &&
        roleMembershipOk(ROLE_EIC, actorContext, paperContext, config.venue_context) &&
        roleMembershipOk(ROLE_AUTHOR, actorContext, paperContext, config.venue_context)
      if (isConflictedEicAuthor) {
        roleContext = ROLE_AUTHOR
        reasons.push('conflicted_eic_author_forced_author_context')
      } else if (roleMembershipOk(explicitRole, actorContext, paperContext, config.venue_context)) {
        roleContext = explicitRole
        reasons.push('explicit_role_context_valid')
      } else {
        reasons.push('explicit_role_context_not_allowed')
      }
    } else {
      fallbackUsed = true
      ;[ROLE_AUTHOR, ROLE_REVIEWER, ROLE_READ_ONLY].some(function(candidate) {
        if (roleMembershipOk(candidate, actorContext, paperContext, config.venue_context)) {
          roleContext = candidate
          reasons.push('direct_forum_fallback_' + candidate)
          return true
        }
        return false
      })
      if (roleContext === ROLE_NONE) reasons.push('direct_forum_no_operational_context')
    }
    return envelope({
      ok: roleContext !== ROLE_NONE,
      context: { role_context: roleContext, entry_point: config.entry_point },
      model: {
        role_context: roleContext,
        entry_point: config.entry_point,
        fallback_used: fallbackUsed,
        allowed_contexts: allowedContexts(actorContext, paperContext, config.venue_context),
        context_reasons: reasons
      },
      reasons: reasons
    })
  }

  function getRoleContextAccessModel(actorContext, paperContext, config) {
    config = config || {}
    paperContext = paperContext || {}
    var requiredRole = config.required_role_context || null
    var requestedRole = config.requested_role_context || entryPointRole(config.entry_point) || null
    var reasons = []
    if (requiredRole && requestedRole !== requiredRole) {
      reasons.push(requestedRole ? 'required_role_context_mismatch' : 'required_role_context_missing')
      return envelope({
        ok: false,
        context: { role_context: requestedRole || ROLE_NONE, required_role_context: requiredRole, entry_point: config.entry_point },
        model: {
          role_context: requestedRole || ROLE_NONE,
          required_role_context: requiredRole,
          allowed_contexts: allowedContexts(actorContext, paperContext, config.venue_context)
        },
        reasons: reasons
      })
    }
    var roleResult = resolveRoleContext(actorContext, paperContext, {
      entry_point: config.entry_point,
      requested_role_context: requestedRole,
      venue_context: config.venue_context
    })
    reasons = roleResult.reasons.slice()
    if (requiredRole && roleResult.model.role_context !== requiredRole) {
      reasons.push('resolved_role_context_mismatch')
    }
    var ok = roleResult.ok && (!requiredRole || roleResult.model.role_context === requiredRole)
    return envelope({
      ok: ok,
      context: { role_context: roleResult.model.role_context, required_role_context: requiredRole, entry_point: config.entry_point },
      model: {
        role_context: roleResult.model.role_context,
        required_role_context: requiredRole,
        allowed_contexts: roleResult.model.allowed_contexts,
        role_context_model: roleResult.model
      },
      reasons: reasons
    })
  }

  function catalogInvitations(desiredCatalog) {
    desiredCatalog = desiredCatalog || {}
    var entries = desiredCatalog.invitations || desiredCatalog.entries || []
    if (!Array.isArray(entries)) return entries
    return entries.reduce(function(acc, entry) {
      if (entry && entry.id) acc[entry.id] = entry
      return acc
    }, {})
  }

  function classifyInvitation(invitation, desiredCatalog, config) {
    config = config || {}
    var now = config.now_millis || Date.now()
    var expdate = invitation && invitation.expdate
    if (expdate !== undefined && expdate !== null && expdate <= now) {
      return { state: 'expired', reasons: ['expired_invitation'] }
    }
    var catalog = catalogInvitations(desiredCatalog)
    var keys = Object.keys(catalog)
    if (keys.length) {
      var entry = catalog[invitation.id]
      if (!entry) return { state: 'unsupported', reasons: ['unsupported_invitation', 'not_in_desired_catalog'] }
      var desired = entry.desired_permissions || {}
      var staleKey = ['readers', 'writers', 'invitees', 'signatures'].find(function(key) {
        return desired[key] && JSON.stringify(asList(invitation[key])) !== JSON.stringify(asList(desired[key]))
      })
      if (staleKey) return { state: 'stale', reasons: ['stale_' + staleKey] }
    }
    return { state: 'current', reasons: [] }
  }

  function matchesInvitees(actorContext, invitation, roleContext, paperContext) {
    var groups = paperContext.groups || {}
    var invitees = asList(invitation && invitation.invitees)
    if (!invitees.length) return { ok: false, reason: 'no_invitees' }
    var roleAllowedInvitees = invitees.filter(function(principal) {
      return inviteeMatchesRoleContext(String(principal), roleContext)
    })
    if (!roleAllowedInvitees.length) return { ok: false, reason: 'role_context_not_invitee' }
    var ok = roleAllowedInvitees.some(function(principal) {
      return matchesPrincipal(actorContext, principal, groups)
    })
    return ok ? { ok: true, reason: 'matched_invitee' } : { ok: false, reason: 'role_context_not_invitee' }
  }

  function inviteeMatchesRoleContext(principal, roleContext) {
    if (principal.indexOf('/Authors') >= 0) return roleContext === ROLE_AUTHOR
    if (principal.indexOf('/Reviewers') >= 0 || principal.indexOf('/Reviewer_') >= 0) return roleContext === ROLE_REVIEWER
    if (principal.indexOf('/Action_Editors') >= 0 || principal.indexOf('/Action_Editor_') >= 0) return roleContext === ROLE_AE
    if (principal.indexOf('/Editors_In_Chief') >= 0) return roleContext === ROLE_EIC
    if (principal.indexOf('/Production_Editors') >= 0) return roleContext === ROLE_PE
    return true
  }

  function matchesSignature(actorContext, signature, roleContext, paperContext) {
    if (matchesPrincipal(actorContext, signature, paperContext.groups || {})) return { ok: true, reason: 'matched_signature' }
    if (roleContext === ROLE_REVIEWER && String(signature).indexOf('/Reviewer_') >= 0) return { ok: true, reason: 'anonymous_reviewer_signature' }
    if (roleContext === ROLE_AE && String(signature).indexOf('/Action_Editor_') >= 0) return { ok: true, reason: 'anonymous_ae_signature' }
    return { ok: false, reason: 'signature_not_allowed_for_role_context' }
  }

  function paperEditorialReaders(paperContext, venueContext) {
    venueContext = venueContext || {}
    if (!paperContext.paper_number) return []
    var venueId = venueContext.venue_id || 'JMLR'
    var roleGroups = venueContext.role_groups || {}
    return unique([
      venueId + '/Paper' + paperContext.paper_number + '/Action_Editors',
      roleGroups.eic || venueId + '/Editors_In_Chief'
    ])
  }

  function getRequiredNoteReaders(paperContext, invitation, config) {
    config = config || {}
    invitation = invitation || {}
    var edit = invitation.edit || {}
    var noteEdit = edit.note || {}
    var desiredCatalog = paperContext.desired_catalog || {}
    var notePolicy = desiredCatalog.note_audience_policy || {}
    var explicit = []
      .concat(asList(edit.required_readers), asList(edit.locked_readers))
      .concat(asList(noteEdit.required_readers), asList(noteEdit.locked_readers))
      .concat(asList(notePolicy.required_readers), asList(notePolicy.locked_readers))
    var reasons = explicit.length ? ['explicit_required_note_readers'] : []
    var required = unique(explicit)
    if (paperContext.enforce_required_editorial_readers || desiredCatalog.required_editorial_note_readers) {
      required = unique(required.concat(paperEditorialReaders(paperContext, config.venue_context)))
      reasons.push('required_editorial_note_readers')
    }
    var locked = unique(required.concat(asList(notePolicy.locked_readers), asList(noteEdit.locked_readers), asList(edit.locked_readers)))
    return {
      required_readers: required,
      locked_readers: locked,
      reasons: unique(reasons),
      role_context: config.role_context
    }
  }

  function getActionFormModel(actorContext, paperContext, invitation, roleContext, config) {
    config = config || {}
    var edit = invitation.edit || {}
    var noteEdit = edit.note || {}
    var signatures = asList(edit.signatures || noteEdit.signatures || invitation.signatures)
    var allowedSignatures = signatures.filter(function(signature) {
      return matchesSignature(actorContext, signature, roleContext, paperContext).ok
    })
    var reasons = allowedSignatures.length === 1 ? [] : ['expected_exactly_one_signature']
    var requiredReaderModel = getRequiredNoteReaders(paperContext, invitation, {
      role_context: roleContext,
      venue_context: config.venue_context
    })
    var requiredReaders = requiredReaderModel.required_readers
    var lockedReaders = requiredReaderModel.locked_readers
    var readerSummary = unique(asList(noteEdit.readers || edit.readers).concat(requiredReaders))
    var model = {
      fields: noteEdit.content || {},
      signature: allowedSignatures.length === 1 ? allowedSignatures[0] : null,
      allowed_signatures: allowedSignatures,
      reader_summary: readerSummary,
      required_readers: requiredReaders,
      locked_readers: lockedReaders,
      audience_options: readerSummary.map(function(reader) {
        return { id: reader, selected: true, locked: lockedReaders.indexOf(reader) >= 0 }
      }),
      submit_target: invitation.id,
      validation_model: {
        role_context: roleContext,
        expected_signatures: allowedSignatures,
        expected_readers: readerSummary,
        required_readers: requiredReaders,
        locked_readers: lockedReaders,
        expected_writers: noteEdit.writers || []
      }
    }
    var item = makeRenderItem('form', invitation.id, {
      role_context: roleContext,
      source: { kind: 'invitation', id: invitation.id },
      data: { signature: model.signature, required_readers: requiredReaders, locked_readers: lockedReaders },
      visible: !reasons.length,
      enabled: !reasons.length,
      reasons: reasons
    })
    return envelope({ ok: !reasons.length, model: model, items: reasons.length ? [] : [item], hidden_items: reasons.length ? [item] : [], reasons: reasons })
  }

  function shouldRenderDebug(env, debug) {
    return !!(debug && DEBUG_ENVS[env])
  }

  var AUTHOR_HIDDEN_DETAIL_FIELDS = {
    assigned_action_editor: true,
    assigned_reviewer: true,
    assigned_reviewers: true,
    reviewer_email: true,
    reviewer_emails: true,
    reviewer_name: true,
    reviewer_names: true,
    reviewer_status: true,
    reviewer_rating: true,
    reviewer_ratings: true,
    authorids: true,
    author_change_summary: true,
    previous_author_names: true,
    current_author_names: true
  }
  var REVIEWER_HIDDEN_DETAIL_FIELDS = Object.assign({}, AUTHOR_HIDDEN_DETAIL_FIELDS, {
    action_editor_email: true,
    action_editor_name: true
  })

  function contentValue(content, key) {
    var value = content && content[key]
    return value && Object.prototype.hasOwnProperty.call(value, 'value') ? value.value : value
  }

  var COMMON_ASSIGNMENT_PERSONAL_EMAIL_DOMAINS = {
    'gmail.com': true,
    'googlemail.com': true,
    'hotmail.com': true,
    'outlook.com': true,
    'live.com': true,
    'icloud.com': true,
    'me.com': true,
    'mac.com': true,
    'yahoo.com': true,
    'proton.me': true,
    'protonmail.com': true
  }

  function normalizeAssignmentText(value) {
    return String(value || '').trim().toLowerCase()
  }

  function extractAssignmentEmails(text) {
    var matches = String(text || '').match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/ig) || []
    return unique(matches.map(function(email) { return String(email).toLowerCase() }))
  }

  function extractAssignmentProfileIds(values) {
    return unique(asList(values).reduce(function(ids, value) {
      String(value || '').split(/[\s,;|()[\]<>]+/).forEach(function(token) {
        if (/^~[A-Za-z0-9_]+[0-9]*$/.test(token)) ids.push(token)
      })
      return ids
    }, []))
  }

  function assignmentEmailDomain(email) {
    var parts = String(email || '').toLowerCase().split('@')
    return parts.length === 2 ? parts[1] : ''
  }

  function nonPersonalAssignmentDomains(domains) {
    return unique(asList(domains).map(function(domain) {
      return String(domain || '').toLowerCase()
    }).filter(function(domain) {
      return domain && !COMMON_ASSIGNMENT_PERSONAL_EMAIL_DOMAINS[domain]
    }))
  }

  function assignmentEdgeWeight(edge, fallback) {
    if (!edge) return fallback
    var weight = Number(edge.weight)
    return isNaN(weight) ? fallback : weight
  }

  function getAssignmentAvailabilityState(edge, nowMillis) {
    if (!edge || edge.label !== 'Unavailable') return { state: 'available', label: 'Available' }
    var weight = Number(edge.weight || 0)
    if (weight && nowMillis && weight <= nowMillis) return { state: 'available', label: 'Available' }
    if (weight) return { state: 'until', label: 'Unavailable until ' + new Date(weight).toISOString().slice(0, 10), until: weight }
    return { state: 'indefinite', label: 'Unavailable indefinitely' }
  }

  function getCandidateAssignmentConflictReasons(submission, candidate) {
    submission = submission || {}
    candidate = candidate || {}
    var content = submission.content || {}
    var authorIds = asList(contentValue(content, 'authorids'))
    var authorListText = String(contentValue(content, 'author_list') || '')
    var authorConflictText = String(contentValue(content, 'conflict_of_interests') || '')
    var candidateId = candidate.id || candidate.tail || candidate.profile_id || ''
    var authorListProfileIds = unique(authorIds.concat(extractAssignmentProfileIds(authorListText)))
    var conflictProfileIds = extractAssignmentProfileIds(authorConflictText)
    var reasons = []
    var addReason = function(code, label) {
      if (!reasons.some(function(reason) { return reason.code === code && reason.label === label })) {
        reasons.push({ code: code, label: label })
      }
    }

    if (assignmentEdgeWeight(candidate.conflictEdge || candidate.conflictData, 0) !== 0) {
      addReason('openreview_positive', 'OpenReview conflict')
    }
    if (candidateId && authorListProfileIds.indexOf(candidateId) >= 0) {
      addReason('author_list', 'Author list')
    }
    if (candidateId && conflictProfileIds.indexOf(candidateId) >= 0) {
      addReason('conflict_list', 'Author-declared conflict list')
    }
    asList(candidate.conflictReasons).forEach(function(reason) {
      if (typeof reason === 'string') addReason('openreview_positive', reason)
      else if (reason && reason.label) addReason(reason.code || 'openreview_positive', reason.label)
    })
    return reasons
  }

  function classifyAssignmentCandidate(submission, candidate, options) {
    candidate = candidate || {}
    options = options || {}
    var activeLoad = Number(candidate.activePaperLoad || 0)
    var maxLoad = candidate.maxPapers === Infinity ? Infinity : Number(candidate.maxPapers || Infinity)
    var availability = candidate.availability || getAssignmentAvailabilityState(candidate.availabilityEdge || candidate.availabilityData, options.nowMillis || Date.now())
    var conflicts = getCandidateAssignmentConflictReasons(submission, candidate)
    var blockers = []
    var addBlocker = function(code, label) {
      blockers.push({ code: code, label: label })
    }
    if (candidate.assigned || candidate.current) addBlocker('current_assignment', 'Current assignment')
    if (!candidate.id && !candidate.tail && !candidate.profile_id) addBlocker('missing_profile', 'No profile')
    if ((candidate.id || candidate.tail || candidate.profile_id || '').indexOf('~') !== 0) addBlocker('missing_profile', 'No OpenReview profile ID')
    if (candidate.active === false) addBlocker('inactive', 'Not active')
    if (maxLoad !== Infinity && activeLoad >= maxLoad) addBlocker('at_max_load', 'At max load')
    if (candidate.cooldown_until && candidate.cooldown_until > (options.nowMillis || Date.now())) {
      addBlocker('in_cooldown', 'In cooldown until ' + new Date(candidate.cooldown_until).toISOString().slice(0, 10))
    }
    asList(candidate.blockers).forEach(function(blocker) {
      if (typeof blocker === 'string') addBlocker('blocked', blocker)
      else if (blocker && blocker.label) addBlocker(blocker.code || 'blocked', blocker.label)
    })
    var hasAuthorConflict = conflicts.some(function(reason) {
      return reason.code === 'author_list' || reason.code === 'conflict_list'
    })
    var hasOpenReviewConflict = conflicts.some(function(reason) {
      return reason.code === 'openreview_positive' || reason.code === 'openreview_conflict_edge'
    })
    var hasConflict = conflicts.length > 0
    var unavailable = availability.state !== 'available'
    var eligible = !hasConflict && !unavailable && !blockers.length
    var conflictKind = hasAuthorConflict ? 'author_conflict' : (hasOpenReviewConflict ? 'openreview_positive' : 'none_detected')
    var conflictLabel = conflictKind === 'author_conflict'
      ? 'Author conflict'
      : (conflictKind === 'openreview_positive' ? 'OpenReview conflict' : 'None detected')
    var severity = eligible
      ? 'eligible'
      : (hasAuthorConflict ? 'author_conflict' : (unavailable ? 'unavailable' : (blockers.length ? 'blocked' : (hasOpenReviewConflict ? 'warning_conflict' : 'blocked'))))
    var quickLabel = eligible
      ? 'Looks eligible'
      : (hasAuthorConflict ? conflictLabel : (unavailable ? 'Unavailable' : (blockers[0] && blockers[0].label || (hasOpenReviewConflict ? conflictLabel : 'Not eligible'))))
    return {
      eligible: eligible,
      severity: severity,
      quickLabel: quickLabel,
      conflict: {
        hasConflict: hasConflict,
        kind: conflictKind,
        label: conflictLabel,
        selectable: !hasAuthorConflict && !unavailable && !blockers.length,
        overridable: conflictKind === 'openreview_positive' && !unavailable && !blockers.length,
        reasons: conflicts
      },
      availability: availability,
      blockers: blockers,
      detailLabels: conflicts.map(function(reason) { return reason.label }).concat(
        unavailable ? [availability.label] : [],
        blockers.map(function(blocker) { return blocker.label })
      )
    }
  }

  function getAssignmentCooldownUntil(assignmentEdges, currentPaperId, cooldownDays, nowMillis) {
    var cooldownMillis = Number(cooldownDays || 0) * 24 * 60 * 60 * 1000
    if (!cooldownMillis) return null
    var now = nowMillis || Date.now()
    var cutoff = now - cooldownMillis
    var latestRecentAssignment = asList(assignmentEdges).reduce(function(latest, edge) {
      if (!edge || edge.ddate || edge.head === currentPaperId || !edge.cdate || edge.cdate < cutoff) return latest
      return !latest || edge.cdate > latest.cdate ? edge : latest
    }, null)
    return latestRecentAssignment ? latestRecentAssignment.cdate + cooldownMillis : null
  }

  function isPreDecisionPaperState(paperState, venueId) {
    venueId = venueId || 'JMLR'
    return [
      venueId + '/Submitted',
      venueId + '/Assigning_AE',
      venueId + '/Assigned_AE',
      venueId + '/Under_Review',
      venueId + '/Decision_Pending'
    ].indexOf(paperState) >= 0
  }

  function paperHasDecision(paperContext, config) {
    config = config || {}
    if (asList(config.decisions).length) return true
    return asList(paperContext && paperContext.notes).some(function(note) {
      return String(note && note.invitation || '').indexOf('/-/Decision') >= 0
    })
  }

  function paperHasActionEditor(paperContext, config) {
    config = config || {}
    if (config.has_action_editor !== undefined) return !!config.has_action_editor
    if (asList(config.paper_action_editors).length) return true
    if (asList(paperContext && paperContext.action_editors).length) return true
    return false
  }

  function getEicPaperActionPolicy(actorContext, paperContext, config) {
    config = config || {}
    paperContext = paperContext || {}
    var venueContext = config.venue_context || {}
    var venueId = venueContext.venue_id || config.venue_id || 'JMLR'
    var roleResult = actorContext ? resolveRoleContext(actorContext, paperContext, {
      entry_point: config.entry_point || 'eic_console',
      requested_role_context: config.requested_role_context || ROLE_EIC,
      venue_context: venueContext
    }) : null
    var roleContext = roleResult ? roleResult.model.role_context : ROLE_EIC
    var state = paperContext.paper_state || contentValue(paperContext.submission && paperContext.submission.content, 'venueid')
    var decisionExists = paperHasDecision(paperContext, config)
    var hasAe = paperHasActionEditor(paperContext, config)
    var showAeAssignment = roleContext === ROLE_EIC &&
      isPreDecisionPaperState(state, venueId) &&
      !decisionExists &&
      (state !== venueId + '/Under_Review' || hasAe)
    var label = showAeAssignment ? (hasAe ? 'Edit action editor assignment' : 'Assign action editor') : null
    return envelope({
      context: { role_context: roleContext, paper_state: state },
      model: {
        role_context: roleContext,
        shared_actions_follow_action_editor: roleContext === ROLE_EIC,
        conflicted_eic_author_uses_author_view: roleContext === ROLE_AUTHOR,
        show_ae_assignment_action: showAeAssignment,
        ae_assignment_label: label,
        pre_decision_state: isPreDecisionPaperState(state, venueId),
        decision_exists: decisionExists,
        has_action_editor: hasAe
      },
      reasons: roleResult ? roleResult.reasons : []
    })
  }

  function noteId(note, fallback) {
    return String(note && (note.id || note.forum) || fallback)
  }

  function noteClass(note) {
    var invitation = String(note && note.invitation || '')
    if (invitation.indexOf('Contact_AE') >= 0 || invitation.indexOf('Author_Note_To_Action_Editor') >= 0) return 'author-to-ae'
    if (invitation.indexOf('Contact_Action_Editor') >= 0 || invitation.indexOf('Reviewer_Note_To_Action_Editor') >= 0) return 'reviewer-to-ae'
    if (invitation.indexOf('Editorial_Comment') >= 0) return 'editorial-comment'
    return 'paper-note'
  }

  function getNoteViewPolicy(actorContext, paperContext, note, roleContext) {
    var readability = matchesReaders(actorContext, note && note.readers, note && note.nonreaders, paperContext.groups || {})
    var model = {
      note_id: note && note.id,
      note_class: noteClass(note),
      readable: readability.ok,
      readers: asList(note && note.readers),
      nonreaders: asList(note && note.nonreaders),
      invitation: note && note.invitation
    }
    return envelope({
      ok: readability.ok,
      context: { role_context: roleContext },
      model: model,
      reasons: readability.ok ? [] : [readability.reason]
    })
  }

  function buildNoteVisibilityModel(actorContext, paperContext, roleContext) {
    var items = []
    var hidden = []
    ;(paperContext.notes || []).forEach(function(note, index) {
      var policy = getNoteViewPolicy(actorContext, paperContext, note, roleContext)
      var id = noteId(note, 'note-' + index)
      var item = makeRenderItem('note-section', id, {
        role_context: roleContext,
        source: { kind: 'note', id: id, invitation: policy.model.invitation },
        data: policy.model,
        visible: policy.ok,
        enabled: policy.ok,
        reasons: policy.reasons
      })
      if (policy.ok) items.push(item)
      else hidden.push(item)
    })
    return envelope({
      context: { role_context: roleContext },
      model: { note_sections: items, hidden_note_count: hidden.length },
      items: items,
      hidden_items: hidden
    })
  }

  function getDetailsView(actorContext, paperContext, roleContext) {
    var policy = (paperContext.desired_catalog || {}).details_visibility_policy || {}
    var hiddenByRole = policy.hidden_fields_by_role || {}
    var hiddenFields = {}
    asList(hiddenByRole[roleContext]).forEach(function(field) { hiddenFields[field] = true })
    if (roleContext === ROLE_AUTHOR) Object.assign(hiddenFields, AUTHOR_HIDDEN_DETAIL_FIELDS)
    if (roleContext === ROLE_REVIEWER) Object.assign(hiddenFields, REVIEWER_HIDDEN_DETAIL_FIELDS)
    var visible = []
    var hidden = []
    var content = paperContext.submission && paperContext.submission.content || {}
    Object.keys(content).forEach(function(key) {
      var isHidden = !!hiddenFields[key]
      var item = makeRenderItem('detail-field', key, {
        label: key.replace(/_/g, ' ').replace(/\b\w/g, function(ch) { return ch.toUpperCase() }),
        role_context: roleContext,
        source: { kind: 'submission', id: paperContext.paper_id, field: key },
        data: { value: contentValue(content, key) },
        visible: !isHidden,
        enabled: false,
        reasons: isHidden ? ['single_blind_or_operational_detail_hidden'] : []
      })
      if (isHidden) hidden.push(item)
      else visible.push(item)
    })
    ;(paperContext.details || []).forEach(function(detail, index) {
      var readability = matchesReaders(actorContext, detail.readers || ['everyone'], detail.nonreaders, paperContext.groups || {})
      var id = String(detail.id || 'details-' + index)
      var item = makeRenderItem('detail-field', id, {
        role_context: roleContext,
        source: { kind: 'details', id: id },
        data: detail,
        visible: readability.ok,
        enabled: false,
        reasons: readability.ok ? [] : [readability.reason]
      })
      if (readability.ok) visible.push(item)
      else hidden.push(item)
    })
    return envelope({
      context: { role_context: roleContext },
      model: { detail_fields: visible, hidden_detail_count: hidden.length },
      items: visible,
      hidden_items: hidden
    })
  }

  function edgeInvitation(edge) {
    return String(edge && edge.invitation || '')
  }

  function edgeTail(edge) {
    return String(edge && edge.tail || '')
  }

  function edgeTime(edge) {
    return edge && (edge.tcdate || edge.cdate || edge.tmdate || edge.mdate) || 0
  }

  function activeEdges(paperContext, invitationFragment) {
    return (paperContext.edges || []).filter(function(edge) {
      return edgeInvitation(edge).indexOf(invitationFragment) >= 0 && !(edge && edge.ddate)
    })
  }

  function notesForInvitationFragment(paperContext, invitationFragment) {
    return (paperContext.notes || []).filter(function(note) {
      return String(note && note.invitation || '').indexOf(invitationFragment) >= 0
    })
  }

  function reviewSignatureTail(note) {
    var signatures = asList(note && note.signatures)
    return signatures.length ? String(signatures[0]) : ''
  }

  function buildEditorialStatusPanels(actorContext, paperContext, roleContext, config) {
    config = config || {}
    var venueId = config.venue_id || config.venueId || 'JMLR'
    var panels = []
    var hidden = []
    var aeEdges = activeEdges(paperContext, '/Action_Editors/-/Assignment')
    var currentAeEdge = aeEdges.length ? aeEdges[0] : null
    var assignmentTime = currentAeEdge ? edgeTime(currentAeEdge) : 0
    var reviewerEdges = activeEdges(paperContext, '/Reviewers/-/Assignment')
    var reviewNotes = notesForInvitationFragment(paperContext, '/-/Review')
    var decisionNotes = notesForInvitationFragment(paperContext, '/-/Decision')
    var decisionTime = decisionNotes.length ? edgeTime(decisionNotes[0]) : 0
    var submittedReviewSignatures = reviewNotes.map(reviewSignatureTail).filter(Boolean)
    var submittedReviewTails = submittedReviewSignatures
      .filter(function(signature) { return signature.indexOf('Reviewer_') >= 0 })
      .map(function(signature) { return signature.split('/').pop().replace('Reviewer_', '') })
    var requiredReviews = Number(config.required_reviewers || paperContext.required_reviewers || 3)
    var reviewProgress = {
      submitted: reviewNotes.length,
      assigned: reviewerEdges.length,
      required: requiredReviews,
      label: reviewNotes.length + ' submitted / ' + reviewerEdges.length + ' assigned; release threshold ' + requiredReviews
    }

    var assignmentPanel = makeRenderItem('status-panel', 'editorial-assignment-status', {
      label: 'Editorial Assignment Status',
      role_context: roleContext,
      source: { kind: 'edge', invitation_fragment: venueId + '/Paper<number>/Action_Editors/-/Assignment' },
      data: {
        current_action_editor: currentAeEdge ? edgeTail(currentAeEdge) : null,
        assignment_date: assignmentTime || null,
        decision_date: decisionTime || null,
        review_progress: reviewProgress
      },
      enabled: false
    })
    if (roleContext === ROLE_EIC) {
      panels.push(assignmentPanel)
    } else {
      assignmentPanel.visible = false
      assignmentPanel.reasons = ['eic_only_status_panel']
      hidden.push(assignmentPanel)
    }

    var nowMillis = config.now_millis || Date.now()
    var reviewerRows = reviewerEdges.map(function(edge) {
      var tail = edgeTail(edge)
      var signatureMatch = submittedReviewSignatures.filter(function(signature) {
        return signature.endsWith('/' + tail) || signature.endsWith(tail) || signature.indexOf(tail) >= 0
      })
      var submitted = signatureMatch.length > 0 || submittedReviewTails.some(function(suffix) { return tail.endsWith(suffix) })
      var submittedNote = submitted ? reviewNotes.find(function(note) {
        var signature = reviewSignatureTail(note)
        return signature.indexOf(tail) >= 0 || signatureMatch.indexOf(signature) >= 0
      }) : null
      var dueDate = 0
      var submittedTime = submittedNote ? edgeTime(submittedNote) : 0
      return {
        reviewer: tail,
        submitted: submitted,
        submitted_date: submittedTime || null,
        due_date: dueDate || null,
        status: submitted ? 'completed' : (dueDate && nowMillis > dueDate ? 'overdue' : 'active')
      }
    })

    var reviewersPanel = makeRenderItem('status-panel', 'reviewer-status', {
      label: 'Reviewer Status',
      role_context: roleContext,
      source: { kind: 'edge', invitation_fragment: venueId + '/Paper<number>/Reviewers/-/Assignment' },
      data: {
        review_progress: reviewProgress,
        reviewers: reviewerRows
      },
      enabled: false
    })
    if (roleContext === ROLE_AE || roleContext === ROLE_EIC) {
      panels.push(reviewersPanel)
    } else {
      reviewersPanel.visible = false
      reviewersPanel.reasons = ['ae_eic_only_status_panel']
      hidden.push(reviewersPanel)
    }

    return envelope({
      context: { role_context: roleContext },
      model: { status_panels: panels, hidden_status_panel_count: hidden.length },
      items: panels,
      hidden_items: hidden
    })
  }

  function getPaperPageModel(actorContext, paperContext, config) {
    config = config || {}
    var roleResult = resolveRoleContext(actorContext, paperContext, config)
    var roleContext = roleResult.model.role_context
    var items = []
    var hidden = []
    var debugItems = []
    ;(paperContext.invitations || []).forEach(function(invitation) {
      var classification = classifyInvitation(invitation, paperContext.desired_catalog, config)
      var allowed = matchesInvitees(actorContext, invitation, roleContext, paperContext)
      var item = makeRenderItem('action', invitation.id, {
        role_context: roleContext,
        source: { kind: 'invitation', id: invitation.id },
        data: { classification: classification.state },
        reasons: classification.reasons.concat(allowed.ok ? [] : [allowed.reason])
      })
      if (classification.state === 'current' && allowed.ok && roleContext !== ROLE_NONE) {
        items.push(item)
      } else if (['stale', 'unsupported', 'expired'].indexOf(classification.state) >= 0 && shouldRenderDebug(config.env || 'prod', config.debug)) {
        item.visible = false
        item.enabled = false
        item.debug_visible = true
        debugItems.push(item)
      } else {
        item.visible = false
        item.enabled = false
        hidden.push(item)
      }
    })
    var noteModel = buildNoteVisibilityModel(actorContext, paperContext, roleContext)
    var detailsModel = getDetailsView(actorContext, paperContext, roleContext)
    var statusModel = buildEditorialStatusPanels(actorContext, paperContext, roleContext, config)
    items = items.concat(noteModel.items, detailsModel.items, statusModel.items)
    hidden = hidden.concat(noteModel.hidden_items, detailsModel.hidden_items, statusModel.hidden_items)
    return envelope({
      ok: roleResult.ok,
      context: { role_context: roleContext, entry_point: config.entry_point, env: config.env || 'prod' },
      model: {
        role_context: roleContext,
        actions: items.filter(function(item) { return item.type === 'action' }),
        note_sections: noteModel.model.note_sections,
        detail_fields: detailsModel.model.detail_fields,
        status_panels: statusModel.model.status_panels,
        role_context_model: roleResult.model
      },
      items: items,
      hidden_items: hidden,
      debug_items: debugItems,
      reasons: roleResult.reasons
    })
  }

  function validateSubmissionContext(edit, invitation, actorContext, paperContext, roleContext, config) {
    config = config || {}
    var classification = classifyInvitation(invitation, config.desired_catalog, config)
    var reasons = classification.reasons.slice()
    if (classification.state !== 'current') reasons.push('invitation_not_current')
    var formModel = getActionFormModel(actorContext, paperContext, invitation, roleContext)
    var expectedSignature = formModel.model.signature
    var submittedNote = edit.note || edit
    var submittedSignatures = asList(submittedNote.signatures)
    var submittedReaders = asList(submittedNote.readers)
    if (!expectedSignature) reasons.push('no_allowed_signature')
    else if (JSON.stringify(submittedSignatures) !== JSON.stringify([expectedSignature])) reasons.push('wrong_role_signature')
    var requiredReaders = asList(formModel.model.required_readers)
    var missingRequiredReaders = requiredReaders.filter(function(reader) { return submittedReaders.indexOf(reader) < 0 })
    if (requiredReaders.length && missingRequiredReaders.length) reasons.push('missing_required_note_readers')
    var allowed = matchesInvitees(actorContext, invitation, roleContext, paperContext)
    if (!allowed.ok) reasons.push(allowed.reason)
    return envelope({
      ok: !reasons.length,
      model: {
        accepted: !reasons.length,
        expected_signature: expectedSignature,
        submitted_signatures: submittedSignatures,
        required_readers: requiredReaders,
        submitted_readers: submittedReaders,
        missing_required_readers: missingRequiredReaders,
        rejection_code: reasons[0] || null
      },
      reasons: reasons
    })
  }

  function emptyModel(name, model, context) {
    var result = {}
    result[name] = model || {}
    return envelope({ context: context || {}, model: result[name] ? model || {} : {} })
  }

  function itemRoleContext(item) {
    item = item || {}
    return item.role_context || item.roleContext || null
  }

  function itemIdentifier(item, fallback) {
    item = item || {}
    return String(
      item.id ||
      item.forum ||
      (item.submission && item.submission.id) ||
      (item.submissionNumber && item.submissionNumber.number) ||
      item.number ||
      fallback
    )
  }

  function itemAuthorIds(item) {
    item = item || {}
    var submission = item.submission || item.note || item
    return asList(contentValue(submission.content || {}, 'authorids'))
  }

  function consoleItemReasons(item, roleContext, actorContext) {
    item = item || {}
    var reasons = []
    var itemRole = itemRoleContext(item)
    if (itemRole && itemRole !== roleContext) reasons.push('wrong_role_context')
    if (item.visible === false) reasons.push('item_marked_not_visible')
    if (item.hiddenOperationally || item.hidden_operationally) reasons.push('operationally_hidden')
    if (item.authored) reasons.push('authored_operational_paper')
    if (roleContext !== ROLE_AUTHOR && actorMatchesAny(actorContext, itemAuthorIds(item))) reasons.push('authored_operational_paper')
    if (item.conflicted) reasons.push('conflicted_operational_paper')
    reasons = reasons.concat(asList(item.reasons).filter(Boolean))
    return unique(reasons)
  }

  function filterConsoleItems(items, itemType, roleContext, config, actorContext) {
    config = config || {}
    var visibleItems = []
    var renderItems = []
    var hiddenItems = []
    var debugItems = []
    var debugAllowed = shouldRenderDebug(config.env || 'prod', config.debug === true)
    ;(items || []).forEach(function(item, index) {
      var itemId = itemIdentifier(item, itemType + '-' + index)
      var reasons = consoleItemReasons(item, roleContext, actorContext)
      var renderItem = makeRenderItem(itemType, itemId, {
        visible: !reasons.length,
        enabled: !reasons.length,
        role_context: itemRoleContext(item) || roleContext,
        data: { item: item },
        reasons: reasons,
        debug_visible: !!(reasons.length && debugAllowed)
      })
      if (reasons.length) {
        if (debugAllowed) debugItems.push(renderItem)
        else hiddenItems.push(renderItem)
        return
      }
      visibleItems.push(item)
      renderItems.push(renderItem)
    })
    return { visibleItems: visibleItems, renderItems: renderItems, hiddenItems: hiddenItems, debugItems: debugItems }
  }

  function getConsoleModel(actorContext, venueContext, roleContext, config) {
    config = config || {}
    var rows = filterConsoleItems(config.rows || [], 'console-row', roleContext, config, actorContext)
    var tasks = filterConsoleItems(config.pending_tasks || config.pendingTasks || [], 'pending-task', roleContext, config, actorContext)
    return envelope({
      context: {
        role_context: roleContext,
        actor_id: actorContext && actorContext.profile_id,
        venue_id: venueContext && venueContext.venue_id
      },
      model: {
        tabs: config.tabs || [],
        rows: rows.visibleItems,
        pending_tasks: tasks.visibleItems,
        hidden_row_count: rows.hiddenItems.length + rows.debugItems.length,
        hidden_task_count: tasks.hiddenItems.length + tasks.debugItems.length
      },
      items: rows.renderItems.concat(tasks.renderItems),
      hidden_items: rows.hiddenItems.concat(tasks.hiddenItems),
      debug_items: rows.debugItems.concat(tasks.debugItems)
    })
  }

  function candidateReasons(candidate, roleContext, paperContext, maxAssignments) {
    candidate = candidate || {}
    var reasons = []
    if (candidate.conflicted || candidate.conflict) reasons.push('candidate_conflicted')
    if (candidate.available === false) reasons.push('candidate_unavailable')
    if (candidate.cooldown_until && candidate.cooldown_until > Date.now()) reasons.push('candidate_in_cooldown')
    var activeLoad = candidate.active_load || candidate.activeLoad || 0
    var maxLoad = candidate.max_load || candidate.maxLoad
    if (maxLoad !== undefined && maxLoad !== null && activeLoad >= maxLoad) reasons.push('candidate_overloaded')
    var content = paperContext.submission && paperContext.submission.content || {}
    var paperTrack = paperContext.track || contentValue(content, 'track')
    if (paperTrack && candidate.track && paperTrack !== candidate.track) reasons.push('candidate_wrong_track')
    if (candidate.role_context && candidate.role_context !== roleContext) reasons.push('candidate_wrong_role_context')
    if (maxAssignments !== undefined && maxAssignments !== null && (candidate.assigned_count || 0) >= maxAssignments) reasons.push('assignment_cap_reached')
    if (candidate.submitted_work && candidate.removal_candidate) reasons.push('candidate_submitted_work_not_removable')
    return unique(reasons)
  }

  function getAssignmentModel(actorContext, paperContext, roleContext, candidates, config) {
    config = config || {}
    var maxAssignments = config.max_assignments || config.max_reviewers
    var controls = [
      makeRenderItem('control', 'reviewer_assignment_status', { label: 'Reviewer assignment status', role_context: roleContext, enabled: [ROLE_AE, ROLE_EIC].indexOf(roleContext) >= 0 }),
      makeRenderItem('control', 'auto_assign', { label: 'Auto-assign Reviewers', role_context: roleContext, enabled: [ROLE_AE, ROLE_EIC].indexOf(roleContext) >= 0 }),
      makeRenderItem('control', 'search_reviewers', { label: 'Search Reviewers', role_context: roleContext, enabled: [ROLE_AE, ROLE_EIC].indexOf(roleContext) >= 0 }),
      makeRenderItem('control', 'invite_new', { label: 'Invite New Reviewer', role_context: roleContext, enabled: [ROLE_AE, ROLE_EIC].indexOf(roleContext) >= 0 })
    ]
    var visibleCandidates = []
    var candidateItems = []
    var hidden = []
    ;(candidates || []).forEach(function(candidate, index) {
      var id = String(candidate.id || candidate.profile_id || candidate.email || 'candidate-' + index)
      var reasons = candidateReasons(candidate, roleContext, paperContext, maxAssignments)
      var item = makeRenderItem('candidate', id, {
        role_context: roleContext,
        source: { kind: 'candidate', id: id },
        data: { candidate: candidate, eligible: !reasons.length },
        visible: !reasons.length,
        enabled: !reasons.length,
        reasons: reasons
      })
      if (reasons.length) hidden.push(item)
      else {
        visibleCandidates.push(candidate)
        candidateItems.push(item)
      }
    })
    return envelope({
      context: { role_context: roleContext },
      model: {
        controls: controls,
        candidates: visibleCandidates,
        candidate_rows: candidateItems,
        current_assignments: config.current_assignments || paperContext.assignments || [],
        hidden_candidate_count: hidden.length,
        max_assignments: maxAssignments
      },
      items: controls.concat(candidateItems),
      hidden_items: hidden
    })
  }

  function getRoleManagementModel(actorContext, venueContext, people) {
    var roleColumns = Object.keys(venueContext.role_groups || {})
    var rows = []
    var items = []
    var hidden = []
    ;(people || []).forEach(function(person, index) {
      var id = String(person.id || person.profile_id || person.email || 'person-' + index)
      var roles = asList(person.roles)
      var reasons = roles.indexOf('ae') >= 0 && roles.indexOf('oss_ae') >= 0 ? ['mutually_exclusive_ae_roles'] : []
      var row = {
        id: id,
        roles: roles.slice().sort(),
        availability_controls: roles.filter(function(role) { return [ROLE_REVIEWER, ROLE_AE, 'oss_ae'].indexOf(role) >= 0 }),
        update_actions: roleColumns.map(function(role) { return 'set_' + role }),
        reasons: reasons
      }
      rows.push(row)
      var item = makeRenderItem('role-row', id, { data: row, visible: !reasons.length, enabled: !reasons.length, reasons: reasons })
      if (reasons.length) hidden.push(item)
      else items.push(item)
    })
    return envelope({
      model: { visible_role_columns: roleColumns, people: rows, mutual_exclusion_rules: [['ae', 'oss_ae']], hidden_row_count: hidden.length },
      items: items,
      hidden_items: hidden
    })
  }

  function getBulkInviteModel(actorContext, venueContext, selectedRole, recipients) {
    var templates = venueContext.bulk_invite_templates || {}
    var roleAllowed = !selectedRole || templates[selectedRole] || (venueContext.role_groups || {})[selectedRole]
    var accepted = []
    var ignored = []
    ;(recipients || []).forEach(function(recipient) {
      if (recipient.openreviewid || recipient.email) accepted.push(recipient)
      else ignored.push({ recipient: recipient, reason: 'missing_openreviewid_or_email' })
    })
    var blocked = []
    if (!roleAllowed) blocked.push('selected_role_not_configured')
    if (!accepted.length) blocked.push('no_valid_recipients')
    return envelope({
      ok: !blocked.length,
      model: {
        selected_role: selectedRole,
        invite_template: templates[selectedRole],
        accepted_recipients: accepted,
        ignored_recipients: ignored,
        send_eligible: !blocked.length,
        blocked_reasons: blocked
      },
      items: accepted.map(function(recipient, index) { return makeRenderItem('recipient', String(index), { data: recipient }) }),
      hidden_items: ignored.map(function(item, index) { return makeRenderItem('recipient', 'ignored-' + index, { visible: false, enabled: false, data: item, reasons: [item.reason] }) }),
      reasons: blocked
    })
  }

  function getPublicationModel(actorContext, venueContext, papers, artifacts) {
    artifacts = artifacts || {}
    var approvedStatus = venueContext.camera_ready_approved_status || (venueContext.venue_id || 'JMLR') + '/Camera_Ready_Approved'
    var pending = []
    var items = []
    var hidden = []
    ;(papers || []).forEach(function(paper, index) {
      var content = paper.content || {}
      var venueid = contentValue(content, 'venueid')
      var id = String(paper.id || paper.forum || paper.number || 'paper-' + index)
      var reasons = venueid === approvedStatus ? [] : ['paper_not_camera_ready_approved']
      var row = {
        paper: paper,
        final_pdf: paper.final_pdf || (artifacts[id] && artifacts[id].final_pdf),
        metadata: artifacts[id] && artifacts[id].metadata,
        publication_year_source: paper.pdate ? 'pdate' : (paper.cdate ? 'cdate' : null),
        download_publication_files_action: { enabled: !reasons.length, effect: 'separate_browser_downloads' },
        mark_published_action: { enabled: !reasons.length, requires_confirmation: true }
      }
      var item = makeRenderItem('publication-row', id, { data: row, visible: !reasons.length, enabled: !reasons.length, reasons: reasons })
      if (reasons.length) hidden.push(item)
      else {
        pending.push(paper)
        items.push(item)
      }
    })
    return envelope({
      model: { pending_publication: pending, publication_rows: items, artifacts: artifacts, hidden_publication_count: hidden.length },
      items: items,
      hidden_items: hidden
    })
  }

  var DEFAULT_REVIEWER_RATING_SCORES = {
    'No rating': 0,
    'Exceeds expectations': 1,
    'Meets expectations': 0,
    'Falls below expectations': -1,
    'Report problem': -2
  }
  var REVIEWER_TIMELINESS_ORDER = ['On time', 'Past due', 'Review not expected']

  function getReviewerRatingLabels(ratingScores) {
    ratingScores = ratingScores || DEFAULT_REVIEWER_RATING_SCORES
    return Object.keys(ratingScores)
  }

  function emptyReviewerStats(ratingScores) {
    ratingScores = ratingScores || DEFAULT_REVIEWER_RATING_SCORES
    var ratingsMap = {}
    getReviewerRatingLabels(ratingScores).forEach(function(label) {
      ratingsMap[label] = 0
    })
    var timelinessMap = {}
    REVIEWER_TIMELINESS_ORDER.forEach(function(label) {
      timelinessMap[label] = 0
    })
    return {
      ratings: [],
      ratingsMap: ratingsMap,
      timelinessMap: timelinessMap,
      averageRating: 0,
      ratingCount: 0,
      ratingTotal: 0
    }
  }

  function addReviewerRating(stats, ratingNote, ratingScores) {
    stats = stats || emptyReviewerStats(ratingScores)
    ratingScores = ratingScores || DEFAULT_REVIEWER_RATING_SCORES
    var content = ratingNote && ratingNote.content || {}
    var rating = contentValue(content, 'rating') || 'No rating'
    if (stats.ratingsMap[rating] === undefined) stats.ratingsMap[rating] = 0
    stats.ratingsMap[rating] += 1
    stats.ratings.push(rating)
    stats.ratingCount += 1
    stats.ratingTotal += Number(ratingScores[rating] || 0)
    stats.averageRating = stats.ratingCount ? stats.ratingTotal / stats.ratingCount : 0
    var timeliness = contentValue(content, 'timeliness')
    if (timeliness) {
      if (stats.timelinessMap[timeliness] === undefined) stats.timelinessMap[timeliness] = 0
      stats.timelinessMap[timeliness] += 1
    }
    return stats
  }

  function reviewerRatingHelpText(ratingScores) {
    ratingScores = ratingScores || DEFAULT_REVIEWER_RATING_SCORES
    return getReviewerRatingLabels(ratingScores).map(function(label) {
      var score = Number(ratingScores[label] || 0)
      return label + ' = ' + (score > 0 ? '+' : '') + score
    }).join('; ')
  }

  function reviewerStatsSummary(stats) {
    stats = stats || emptyReviewerStats()
    if (!stats.ratingCount) return 'No rating history'
    var timeliness = REVIEWER_TIMELINESS_ORDER.map(function(label) {
      return stats.timelinessMap && stats.timelinessMap[label] || 0
    }).join(' / ')
    return 'Rating ' + stats.averageRating.toFixed(2) + ' (' + stats.ratingCount + '); Timeliness ' + timeliness
  }

  function getReviewerEffectiveDueDate(reviewInvitation, paperReviewDueDate) {
    var candidates = []
    var invitationDueDate = reviewInvitation && reviewInvitation.duedate
    if (invitationDueDate) candidates.push(Number(invitationDueDate))
    if (paperReviewDueDate) candidates.push(Number(paperReviewDueDate))
    candidates = candidates.filter(function(value) {
      return Number.isFinite(value) && value > 0
    })
    return candidates.length ? Math.max.apply(null, candidates) : 0
  }

  function getReviewerTimelinessStatus(review, reviewInvitation, paperReviewDueDate, decisionTime) {
    var effectiveDueDate = getReviewerEffectiveDueDate(reviewInvitation, paperReviewDueDate)
    if (decisionTime && effectiveDueDate && decisionTime <= effectiveDueDate && (!review || !review.tcdate || review.tcdate > decisionTime)) {
      return 'Review not expected'
    }
    if (!review || !review.tcdate) return effectiveDueDate ? 'Past due' : 'Review not expected'
    return effectiveDueDate && review.tcdate > effectiveDueDate ? 'Past due' : 'On time'
  }

  function getActionEditorDecisionTiming(assignmentEdge, decisionNote, nowMillis) {
    var assignmentTime = assignmentEdge && (assignmentEdge.cdate || assignmentEdge.tcdate)
    var decisionTime = decisionNote && (decisionNote.cdate || decisionNote.tcdate || decisionNote.mdate)
    nowMillis = nowMillis || Date.now()
    if (!assignmentTime) {
      return {
        has_timing: false,
        timing_source: 'missing_assignment_edge',
        assignment_time: 0,
        decision_time: decisionTime || 0,
        elapsed: 0,
        completed: !!decisionNote
      }
    }
    var endTime = decisionTime || nowMillis
    return {
      has_timing: true,
      timing_source: 'assignment_edge',
      assignment_time: assignmentTime,
      decision_time: decisionTime || 0,
      elapsed: Math.max(endTime - assignmentTime, 0),
      completed: !!decisionNote
    }
  }

  function getSelectedPaperActionEditorModel(row, assignmentEdge, nowMillis) {
    row = row || {}
    var actionEditor = row.actionEditorProgressData && row.actionEditorProgressData.actionEditor || {}
    var reviewProgress = row.reviewProgressData || {}
    var decisionProgress = row.actionEditorProgressData || {}
    var assignmentTime = assignmentEdge && (assignmentEdge.cdate || assignmentEdge.tcdate)
    return envelope({
      model: {
        current_action_editor: actionEditor,
        assignment_edge: assignmentEdge || null,
        assignment_time: assignmentTime || 0,
        assigned_days: assignmentTime ? Math.floor(Math.max((nowMillis || Date.now()) - assignmentTime, 0) / (24 * 60 * 60 * 1000)) : null,
        assigned_reviewers: reviewProgress.numReviewers || 0,
        required_reviewers: reviewProgress.requiredReviewers || reviewProgress.numReviewers || 0,
        submitted_reviews: reviewProgress.numSubmittedReviews || 0,
        pending_reviews: Math.max((reviewProgress.numReviewers || 0) - (reviewProgress.numSubmittedReviews || 0), 0),
        decision_status: decisionProgress.recommendation || (decisionProgress.decisionPending ? 'Decision pending' : 'No decision'),
        past_due: !!reviewProgress.isPastDue
      }
    })
  }

  function renderVenueHomepageStrip(config) {
    config = config || {}
    var jq = config.jquery || config.$ || (typeof $ !== 'undefined' ? $ : null)
    if (!jq) return false
    var venueId = config.venueId || config.venue_id || 'JMLR'
    var label = config.label || 'Go to JMLR homepage'
    var container = config.container || '#group-container'
    var stripId = config.stripId || 'jmlr-venue-homepage-strip'
    var containerId = stripId + '-container'
    var styleId = stripId + '-style'
    var href = '/group?id=' + encodeURIComponent(venueId)
    if (!jq('#' + styleId).length) {
      jq('head').append(
        '<style id="' + styleId + '">' +
          (config.hideEditBanner === false ? '' : '#edit-banner { display: none !important; }') +
          '#' + containerId + ' { margin: 0; padding: 0; }' +
          '#' + stripId + ' { background: #f2dede; border: 0; border-top: 1px solid #ebccd1; border-bottom: 1px solid #ebccd1; box-sizing: border-box; color: #a94442; margin: 0; padding: 8px 15px; position: relative; width: 100%; }' +
          '#' + stripId + ' a { color: #8a1f11; font-weight: 600; }' +
        '</style>'
      )
    }
    jq('#' + containerId).remove()
    jq(container).prepend(
      '<div id="' + containerId + '">' +
        '<div id="' + stripId + '">' +
          '<a href="' + href + '">' + label + '</a>' +
        '</div>' +
      '</div>'
    )
    function getBootstrapContentInset(viewportWidth) {
      if (viewportWidth >= 1200) return Math.round((viewportWidth - 1170) / 2 + 15)
      if (viewportWidth >= 992) return Math.round((viewportWidth - 970) / 2 + 15)
      if (viewportWidth >= 768) return Math.round((viewportWidth - 750) / 2 + 15)
      return 15
    }
    function syncStripLayout() {
      var stripContainer = jq('#' + containerId)
      var strip = jq('#' + stripId)
      var nav = jq('nav').first()
      if (!stripContainer.length || !strip.length || !nav.length) return
      if (!strip[0].getBoundingClientRect || !nav[0].getBoundingClientRect) return
      var documentElement = typeof document !== 'undefined' && document && document.documentElement
      var navRect = nav[0].getBoundingClientRect()
      var viewportWidth = navRect && navRect.width
        ? Math.round(navRect.width)
        : (documentElement && documentElement.clientWidth
          ? documentElement.clientWidth
        : (typeof globalThis !== 'undefined' && globalThis.innerWidth ? globalThis.innerWidth : stripContainer[0].getBoundingClientRect().width)
        )
      var parentRect = stripContainer.parent().length && stripContainer.parent()[0].getBoundingClientRect
        ? stripContainer.parent()[0].getBoundingClientRect()
        : { left: 0 }
      var contentInset = getBootstrapContentInset(viewportWidth)
      strip.css({
        left: Math.round((navRect && navRect.left ? navRect.left : 0) - parentRect.left) + 'px',
        width: Math.round(viewportWidth) + 'px',
        'padding-left': contentInset + 'px',
        'padding-right': contentInset + 'px'
      })
      stripContainer.css('margin-top', '0px')
      var gap = Math.round(strip[0].getBoundingClientRect().top - navRect.bottom)
      stripContainer.css('margin-top', gap > 0 ? (-gap) + 'px' : '0px')
    }
    syncStripLayout()
    var eventTarget = typeof globalThis !== 'undefined'
      ? globalThis
      : (typeof window !== 'undefined' ? window : null)
    if (eventTarget && eventTarget.addEventListener) {
      eventTarget.addEventListener('resize', syncStripLayout)
    }
    return true
  }

  return {
    ROLE_AUTHOR: ROLE_AUTHOR,
    ROLE_REVIEWER: ROLE_REVIEWER,
    ROLE_AE: ROLE_AE,
    ROLE_EIC: ROLE_EIC,
    ROLE_PE: ROLE_PE,
    ROLE_READ_ONLY: ROLE_READ_ONLY,
    ROLE_NONE: ROLE_NONE,
    envelope: envelope,
    makeRenderItem: makeRenderItem,
    normalizeActor: normalizeActor,
    isGroupMember: isGroupMember,
    matchesReaders: matchesReaders,
    loadActorContext: loadActorContext,
    loadPaperContext: loadPaperContext,
    loadVenueContext: loadVenueContext,
    resolveRoleContext: resolveRoleContext,
    getRoleContextAccessModel: getRoleContextAccessModel,
    getRoleRouterModel: function(actorContext, venueContext) { return emptyModel('router', { paper_actions: [] }) },
    getConsoleModel: getConsoleModel,
    getPaperPageModel: getPaperPageModel,
    getActionFormModel: getActionFormModel,
    validateSubmissionContext: validateSubmissionContext,
    getRequiredNoteReaders: getRequiredNoteReaders,
    getNoteViewPolicy: getNoteViewPolicy,
    buildNoteVisibilityModel: buildNoteVisibilityModel,
    getDetailsView: getDetailsView,
    buildEditorialStatusPanels: buildEditorialStatusPanels,
    getAssignmentModel: getAssignmentModel,
    getRoleManagementModel: getRoleManagementModel,
    getBulkInviteModel: getBulkInviteModel,
    getPublicationModel: getPublicationModel,
    DEFAULT_REVIEWER_RATING_SCORES: DEFAULT_REVIEWER_RATING_SCORES,
    REVIEWER_TIMELINESS_ORDER: REVIEWER_TIMELINESS_ORDER,
    emptyReviewerStats: emptyReviewerStats,
    addReviewerRating: addReviewerRating,
    reviewerRatingHelpText: reviewerRatingHelpText,
    reviewerStatsSummary: reviewerStatsSummary,
    getReviewerEffectiveDueDate: getReviewerEffectiveDueDate,
    getReviewerTimelinessStatus: getReviewerTimelinessStatus,
    getActionEditorDecisionTiming: getActionEditorDecisionTiming,
    getSelectedPaperActionEditorModel: getSelectedPaperActionEditorModel,
    getAssignmentAvailabilityState: getAssignmentAvailabilityState,
    getCandidateAssignmentConflictReasons: getCandidateAssignmentConflictReasons,
    classifyAssignmentCandidate: classifyAssignmentCandidate,
    getAssignmentCooldownUntil: getAssignmentCooldownUntil,
    renderPreviousSubmissionsList: renderPreviousSubmissionsList,
    getPublicationLifecycleLabel: getPublicationLifecycleLabel,
    isPublishedPublicationLifecycle: isPublishedPublicationLifecycle,
    renderVenueHomepageStrip: renderVenueHomepageStrip,
    getEicPaperActionPolicy: getEicPaperActionPolicy,
    getRepairReportModel: function(repairDiff) { return envelope({ model: repairDiff || {} }) },
    classifyInvitation: classifyInvitation,
    matchesInvitees: matchesInvitees,
    matchesSignature: matchesSignature,
    shouldRenderDebug: shouldRenderDebug
  }
})
