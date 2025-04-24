async function process(client, edge, invitation) {
  client.throwErrors = true

  const { groups } = await client.getGroups({ id: edge.domain })
  const domain = groups[0]
  const reviewersId = invitation.content.match_group?.value
  const assignmentInvitationId = invitation.content.assignment_invitation_id?.value
  const conflictInvitationId = invitation.content.conflict_invitation_id?.value
  const assignmentLabel = invitation.content.assignment_label?.value
  const inviteLabel = invitation.content.invite_label?.value
  const conflictPolicy = domain.content.reviewers_conflict_policy?.value
  const conflictNYears = domain.content.reviewers_conflict_n_years?.value
  const reviewersName = reviewersId.split('/').pop().toLowerCase()
  const quota = domain.content?.['submission_assignment_max_' + reviewersName]?.value
  const profileReqs = domain.content.invited_reviewer_profile_minimum_requirements?.value

  if (edge.ddate && edge.label !== inviteLabel) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `Cannot cancel the invitation since it has status: "${edge.label}"` }))
  }

  if (edge.label !== inviteLabel) {
    return
  }

  const { notes } = await client.getNotes({ id: edge.head })
  const submission = notes[0]

  const profiles = await client.tools.getProfiles([edge.tail], true)
  const userProfile = profiles[0]

  // Check for complete profile, if no profile then go to pending sign up
  if (profileReqs && !userProfile.id.includes('@')) {
    let isIncomplete = false;

    for (const [profilePath, expectedValue] of Object.entries(profileReqs)) {
      const pathItems = profilePath.split('.');
      let actualValue = userProfile;

      // Resolve actual value from the profile
      for (const item of pathItems) {
        if (actualValue && typeof actualValue === 'object') {
          actualValue = actualValue?.[item];
        } else {
          actualValue = null;
        }
  
        if (actualValue === null || actualValue === undefined) {
          break;
        }
      }

      // If checking publications, filter notes for pdate
      if (pathItems[pathItems.length - 1] === 'publications') {
        actualValue = actualValue.filter(pub => pub.hasOwnProperty('pdate'));
      }

      // Check against requirement
      // Check number of entries
      if (typeof expectedValue === 'number') {
        if (actualValue?.length < expectedValue) {
          isIncomplete = true;
          break;
        }
      // Check if field exists in profile (e.g. links)
      } else if (expectedValue === true && !actualValue) {
        isIncomplete = true;
        break;
      } else {
        console.log(`Invalid path: ${profilePath}`);
      }
    }

    if (isIncomplete) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not invite ${userProfile.id}, the user has an incomplete profile according to venue standards` }))
    }
  }

  if (userProfile.id !== edge.tail) {
    const { edges } = await client.getEdges({ invitation: edge.invitation, head: edge.head, tail: userProfile.id })
    if (edges.length) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not invite ${userProfile.id}, the user is already invited` }))
    }
  }

  const { edges } = await client.getEdges({ invitation: assignmentInvitationId, head: edge.head, tail: userProfile.id, label: assignmentLabel })
  if (edges.length) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not invite ${userProfile.id}, the user is already assigned` }))
  }

  if (quota) {
    const acceptLabel = invitation?.content?.accepted_label?.value ?? '';
    const declineLabel = invitation?.content?.declined_label?.value ?? '';
    const filteredLabels = [acceptLabel, declineLabel];
    
    const [{ edges: inviteAssignmentEdges }, { edges: assignmentEdges }] = await Promise.all([
      client.getEdges({ invitation: edge.invitation, head: edge.head }),
      client.getEdges({ invitation: assignmentInvitationId, head: edge.head })
    ])

    // Filter invite assignment edges to exclude edges that are accepted and the current edge.id
    const filteredInviteAssignmentEdges = inviteAssignmentEdges.filter(e => !filteredLabels.includes(e?.label ?? '') && e.id !== edge.id)

    if (filteredInviteAssignmentEdges.length + assignmentEdges.length >= quota) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not invite assignment, total assignments and invitations must not exceed ${quota}; invite edge ids=${filteredInviteAssignmentEdges.map(e=>e.id)} assignment edge ids=${assignmentEdges.map(e=>e.id)}` }))
    }
  }

  if (userProfile.id.startsWith('~')) {
    const { groups: reviewersGroup } = await client.getGroups({ id: reviewersId, member: userProfile.id })

    if (reviewersGroup.length) {
      const { edges } = await client.getEdges({ invitation: conflictInvitationId, head: edge.head, tail: userProfile.id })
      if (edges.length) {
        return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not invite ${userProfile.id}, the user has a conflict` }))
      }

      if (assignmentLabel) {
        return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not invite ${userProfile.id}, the user is an official reviewer` }))
      }
    }
  }
 
  const authorProfiles = await client.tools.getProfiles(submission.content.authorids?.value, true)
  const conflicts = await client.tools.getConflicts(authorProfiles, userProfile, conflictPolicy, conflictNYears)
  if (conflicts.length) { 
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not invite ${userProfile.id}, the user has a conflict` }))
  }
}