async function process(client, edge, invitation) {
  client.throwErrors = false

  const { groups } = await client.getGroups({ id: edge.domain })
  const domain = groups[0]
  const venueId = domain.id
  const submissionName = domain.content.submission_name?.value
  const reviewName = invitation.content.review_name?.value
  const reviewersAnonName = invitation.content.reviewers_anon_name?.value
  const reviewersName = invitation.content.reviewers_name?.value
  const quota = domain.content?.['submission_assignment_max_' + reviewersName.toLowerCase()]?.value
  const inviteAssignmentId = domain.content?.[reviewersName.toLowerCase() + '_invite_assignment_id']?.value

  const { notes } = await client.getNotes({ id: edge.head })
  const submission = notes[0]
  const submissionGroupId = `${venueId}/${submissionName}${submission.number}`

  if (!edge.ddate) {
    const [{ edges: inviteAssignmentEdges }, { edges: assignmentEdges }] = await Promise.all([
        client.getEdges({ invitation: inviteAssignmentId, head: edge.head }),
        client.getEdges({ invitation: edge.invitation, head: edge.head })
    ])

    if (quota && inviteAssignmentEdges.length + assignmentEdges.length >= quota) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not make assignment, total assignments and invitations must not exceed ${quota}` }))
    }
    const { count } = await client.getGroups({ id: `${submissionGroupId}/${reviewersName}` })
    if ( count === 0) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not make assignment, submission ${reviewersName} group not found.` }))
    }
    return
  }

  if (reviewersAnonName) {
    const { groups: anonGroups, count: groupCount } = await client.getGroups({ prefix: `${submissionGroupId}/${reviewersAnonName}`, signatory: edge.tail })

    if (groupCount === 0) { 
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can remove assignment, signatory groups not found for ${edge.tail}` }))
    }

    const { count: noteCount } = await client.getNotes({ invitation: `${submissionGroupId}/-/` + reviewName, signatures: anonGroups[0].id })

    if (noteCount > 0) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not remove assignment, the user ${edge.tail} already posted a ${reviewName.replace('_', ' ')}` }))
    }
  }
}