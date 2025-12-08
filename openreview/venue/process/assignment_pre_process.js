async function process(client, edge, invitation) {
  client.throwErrors = false

  const { groups } = await client.getGroups({ id: edge.domain })
  const domain = groups[0]
  const venueId = domain.id
  const submissionName = domain.content.submission_name?.value
  const reviewName = invitation.content.review_name?.value
  const reviewersAnonName = invitation.content.reviewers_anon_name?.value
  const committeeName = invitation.content.reviewers_name?.value
  const committeeRole = invitation.content.committee_role?.value
  const quota = domain.content?.[`submission_assignment_max_${committeeRole}`]?.value
  const inviteAssignmentId = domain.content?.[`${committeeRole}_invite_assignment_id`]?.value

  const { notes } = await client.getNotes({ id: edge.head })
  const submission = notes[0]
  const submissionGroupId = `${venueId}/${submissionName}${submission.number}`

  if (!edge.ddate) {
    const { invitations } = await client.getInvitations({ id: inviteAssignmentId });
    const acceptLabel = invitations[0]?.content?.accepted_label?.value ?? '';
    const invitedLabel = invitations[0]?.content?.invited_label?.value ?? '';
    const pendingSignUpLabel = 'Pending Sign Up';
    const includedLabels = [acceptLabel, invitedLabel, pendingSignUpLabel];

    const [{ edges: inviteAssignmentEdges }, { edges: assignmentEdges }] = await Promise.all([
        client.getEdges({ invitation: inviteAssignmentId, head: edge.head }),
        client.getEdges({ invitation: edge.invitation, head: edge.head })
    ])

    // Filter assignment edges to exclude the current edge.id
    const filteredAssignmentEdges = assignmentEdges.filter(e => e.id !== edge.id)
    // Convert includedLabels to lowercase for case-insensitive comparison
    const lowerCaseIncludedLabels = includedLabels.map(label => label.toLowerCase());
    const assignmentTails = filteredAssignmentEdges.map(e => e.tail);
    
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
    // Bypass quota if edge comes from invite assignment (invites should always be able to be accepted)
    const inviteAssignmentTails = inviteAssignmentEdges.map(e => e.tail)
    const bypassQuota = inviteAssignmentTails.includes(edge.tail)

    if (!bypassQuota && quota && filteredInviteAssignmentEdges.length + filteredAssignmentEdges.length >= quota) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not make assignment, total assignments and invitations must not exceed ${quota}; invite edges=${filteredInviteAssignmentEdges.length} assignment edges=${filteredAssignmentEdges.length}` }))
    }
    const { count } = await client.getGroups({ id: `${submissionGroupId}/${committeeName}` })
    if ( count === 0) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not make assignment, submission ${committeeName} group not found.` }))
    }
    return
  }

  if (reviewersAnonName) {
    const { groups: anonGroups } = await client.getGroups({ prefix: `${submissionGroupId}/${reviewersAnonName}`, signatory: edge.tail })

    if (!anonGroups?.length) { 
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can remove assignment, signatory groups not found for ${edge.tail}` }))
    }

    const { notes } = await client.getNotes({ invitation: `${submissionGroupId}/-/` + reviewName, signatures: anonGroups[0].id, limit: 1 })

    if (notes?.length > 0) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not remove assignment, the user ${edge.tail} already posted a ${reviewName.replace('_', ' ')}` }))
    }
  }
}