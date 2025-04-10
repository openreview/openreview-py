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
    const declineLabel = invitation?.content?.declined_label?.value ?? '';
    const filteredLabels = [acceptLabel, declineLabel];
    
    const [{ edges: inviteAssignmentEdges }, { edges: assignmentEdges }] = await Promise.all([
      client.getEdges({ invitation: edge.invitation, head: edge.head }),
      client.getEdges({ invitation: assignmentInvitationId, head: edge.head })
    ])

    // Convert filteredLabels to lowercase for case-insensitive comparison
    const lowerCaseFilteredLabels = filteredLabels.map(label => label.toLowerCase());
    
    // Filter invite assignment edges to exclude edges that do not contain any of the filteredLabels as substrings (case-insensitive) and the current edge.id
    const filteredInviteAssignmentEdges = inviteAssignmentEdges.filter(e => {
      const edgeLabel = e?.label?.toLowerCase() ?? '';
      // Check if edgeLabel includes any of the filteredLabels
      const includesFilteredLabel = lowerCaseFilteredLabels.some(filteredLabel => edgeLabel.includes(filteredLabel));
      // Include edge only if it contains any of the filteredLabels and is not the current edge
      return !includesFilteredLabel && e.id !== edge.id;
    });

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