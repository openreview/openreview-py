async function process(client, edit, invitation) {
  client.throwErrors = true
 
  const committeeInvitedId = invitation.content.committee_invited_id?.value
  const inviteAssignmentInvitation = invitation.content.invite_assignment_invitation_id?.value
  const hashSeed = invitation.content.hash_seed?.value
  
  const { groups: domainGroups } = await client.getGroups({ id: invitation.domain })
  const domain = domainGroups[0]
  const submissionVenueId = domain.content.submission_venue_id.value
  
  const note = edit.note
  const user = decodeURIComponent(note.content.user.value)
  const hashkey = crypto.createHmac('sha256', hashSeed)
                      .update(user)
                      .digest('hex');

  if (hashkey != note.content.key.value) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'Wrong key, please refer back to the recruitment email' }))
  }

  const { notes } = await client.getNotes({ id: note.content.submission_id.value })
  const submission = notes[0]

  const { count: edgeCount, edges } = await client.getEdges({ invitation: inviteAssignmentInvitation, head: submission.id, tail: note.content.user.value })
  let inviteEdges = edges

  if (edgeCount === 0) {
    const { profiles} = await client.getProfiles(user.startsWith('~') ? { id: user } : { email: user })
    if (profiles.length > 0) {
      const { count: edgeCount, edges } = await client.getEdges({ invitation: inviteAssignmentInvitation, head: submission.id, tail: profiles[0].id })
      inviteEdges = edges
      if (edgeCount == 0) {
        return Promise.reject(new OpenReviewError({ name: 'Error', message: 'Invitation no longer exists. No action is required from your end.' }))
      }
    }
  }

  const { count: groupCount } = await client.getGroups({ id: committeeInvitedId, member: user })
  if (groupCount == 0) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'User not in invited group, please accept the invitation using the email address you were invited with' }))
  }

  if (submission.content.venueid.value != submissionVenueId) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'This submission is no longer under review. No action is required from your end.' }))
  }

  if (note.content.response.value == 'Yes') {
    const label = inviteEdges[0].label
    if (label == 'Accepted') {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: 'You have already accepted this invitation.' }))
    }
    if (label == 'Pending Sign Up') {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: 'You have already accepted this invitation, but the assignment is pending until you create a profile and no conflict are detected.' }))
    }
    if (label == 'Conflict Detected') {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: 'You have already accepted this invitation, but a conflict was detected and the assignment cannot be made.' }))
    }
  }

  if (note.content.response.value == 'No') {
    const label = inviteEdges[0].label
    if (label == 'Declined' && !note.content.comment) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: 'You have already declined this invitation.' }))
    }
  }

}
