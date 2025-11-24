async function process(client, edge, invitation) {
  client.throwErrors = true

  const { groups } = await client.getGroups({ id: edge.domain })
  const domain = groups[0]
  const reviewersId = invitation.content.match_group?.value
  const assignmentInvitationId = invitation.content.assignment_invitation_id?.value
  const conflictInvitationId = invitation.content.conflict_invitation_id?.value
  const assignmentLabel = invitation.content.assignment_label?.value
  const committeeRole = invitation.content.committee_role?.value
  const inviteLabel = invitation.content.invite_label?.value
  const committeeName = reviewersId?.split("/")?.pop()
  const conflictPolicy = domain.content?.[`${committeeRole}_conflict_policy`]?.value
  const conflictNYears = domain.content?.[`${committeeRole}_conflict_n_years`]?.value
  const quota = domain.content?.[`submission_assignment_max_${committeeRole}`]?.value

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
    const invitedLabel = invitation?.content?.invited_label?.value ?? '';
    const pendingSignUpLabel = 'Pending Sign Up';
    const includedLabels = [acceptLabel, invitedLabel, pendingSignUpLabel];
    
    const [{ edges: inviteAssignmentEdges }, { edges: assignmentEdges }] = await Promise.all([
      client.getEdges({ invitation: edge.invitation, head: edge.head }),
      client.getEdges({ invitation: assignmentInvitationId, head: edge.head })
    ])

    // Convert includedLabels to lowercase for case-insensitive comparison
    const lowerCaseIncludedLabels = includedLabels.map(label => label.toLowerCase());
    const assignmentTails = assignmentEdges.map(e => e.tail);
    
    // Filter invite assignment edges to include only edges that contain any of the includedLabels as substrings (case-insensitive) and exclude the current edge.id
    const filteredInviteAssignmentEdges = inviteAssignmentEdges.filter(e => {
      const edgeLabel = e?.label?.toLowerCase() ?? '';
      // Check if edgeLabel includes any of the includedLabels
      const includesIncludedLabel = lowerCaseIncludedLabels.some(includedLabel => edgeLabel.includes(includedLabel));
      // Exclude if it already has a corresponding assignment edge (same tail)
      const hasCorrespondingAssignment = assignmentTails.includes(e.tail);
      // Include edge only if it contains any of the includedLabels, is not the current edge, and doesn't have a corresponding assignment
      return includesIncludedLabel && e.id !== edge.id && !hasCorrespondingAssignment;
    });
    const alreadyPosted = inviteAssignmentEdges.filter(e => e.id === edge.id).length > 0

    if (!alreadyPosted && filteredInviteAssignmentEdges.length + assignmentEdges.length >= quota) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not invite assignment, total assignments and invitations must not exceed ${quota}; invite edges=${filteredInviteAssignmentEdges.length} assignment edges=${assignmentEdges.length}` }))
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