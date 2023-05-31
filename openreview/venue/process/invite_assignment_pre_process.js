async function process(client, edge, invitation) {
  client.throwErrors = true

  const { groups } = await client.getGroups({ id: edge.domain })
  const domain = groups[0]
  const reviewersId = invitation.content.match_group?.value
  const assignmentInvitationId = invitation.content.assignment_invitation_id?.value
  const conflictInvitationId = invitation.content.conflict_invitation_id?.value
  const assignmentLabel = invitation.content.assignment_label?.value
  const inviteLabel = invitation.content.invite_label?.value
  const conflictPolicy = invitation.content.reviewers_conflict_policy?.value
  const conflictNYears = invitation.content.reviewers_conflict_n_years?.value

  if (edge.ddate) {
    return
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