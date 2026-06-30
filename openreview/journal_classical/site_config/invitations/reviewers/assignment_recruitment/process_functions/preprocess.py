async function process(client, edit, invitation) {
  client.throwErrors = true

  const inviteAssignmentInvitation = invitation.content.invite_assignment_invitation_id?.value
  const hashSeed = invitation.content.hash_seed?.value

  const note = edit.note
  const invitedUser = decodeURIComponent(note.content.user.value)
  const edgeId = note.content.edge_id?.value
  const hashkey = crypto.createHmac('sha256', hashSeed)
                      .update(invitedUser)
                      .digest('hex')

  if (hashkey != note.content.key.value) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'Wrong key, please refer back to the recruitment email' }))
  }

  const { notes } = await client.getNotes({ id: note.content.submission_id.value })
  const submission = notes[0]
  const venueId = inviteAssignmentInvitation.split('/Reviewers/')[0]
  const readers = [`${venueId}/Editors_In_Chief`]
  const addReader = (reader) => {
    if (reader && !readers.includes(reader)) readers.push(reader)
  }
  const addValidReader = (reader) => {
    if (reader && (reader.startsWith('~') || reader.startsWith(`${venueId}/`))) addReader(reader)
  }

  addValidReader(invitedUser)
  addValidReader(note.content.inviter?.value)
  for (const signature of (note.signatures || [])) {
    addValidReader(signature)
  }
  note.readers = readers
  note.nonreaders = [`${venueId}/Paper${submission.number}/Authors`]

  const identities = [invitedUser]
  const addIdentity = (identity) => {
    if (identity && !identities.includes(identity)) identities.push(identity)
  }

  for (const signature of (note.signatures || [])) {
    if (signature && signature.startsWith('~')) addIdentity(signature)
  }

  try {
    const { profiles } = await client.getProfiles(invitedUser.startsWith('~') ? { id: invitedUser } : { email: invitedUser })
    for (const profile of (profiles || [])) {
      addIdentity(profile.id)
    }
  } catch (error) {
    // The invited email may not be attached to the logged-in profile. The process
    // script will make the final logged-in-profile decision.
  }

  let inviteEdges = []
  const addInviteEdges = (edges) => {
    for (const edge of (edges || [])) {
      if (!inviteEdges.find((candidate) => candidate.id === edge.id)) {
        inviteEdges.push(edge)
      }
    }
  }

  for (const identity of identities) {
    const { edges } = await client.getEdges({ invitation: inviteAssignmentInvitation, head: submission.id, tail: identity, trash: true })
    addInviteEdges(edges)
  }

  if (edgeId && !inviteEdges.find((candidate) => candidate.id === edgeId)) {
    const { edges } = await client.getEdges({ id: edgeId, trash: true })
    addInviteEdges((edges || []).filter((candidate) => (
      candidate.invitation === inviteAssignmentInvitation && candidate.head === submission.id
    )))
  }

  if (!inviteEdges.length) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: {{MESSAGE_TEMPLATE_JSON:recruitment/invitation_unavailable.txt}} }))
  }

  const response = note.content.response.value
  const edge = inviteEdges.find((candidate) => candidate.id === edgeId) ||
    inviteEdges.find((candidate) => candidate.label === 'Invitation Sent') ||
    inviteEdges.find((candidate) => candidate.label === 'Accepted - Action Failed') ||
    inviteEdges[0]
  const label = edge && edge.label
  const unavailableInvitationMessage = {{MESSAGE_TEMPLATE_JSON:recruitment/invitation_unavailable.txt}}
  const { notes: existingResponseNotes } = await client.getNotes({
    invitation: invitation.id,
    content: { edge_id: edge.id },
    trash: true
  })
  const existingResponses = (existingResponseNotes || [])
    .map((responseNote) => responseNote.content?.response?.value)
    .filter(Boolean)

  if (existingResponses.includes('Yes')) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: unavailableInvitationMessage }))
  }

  if (existingResponses.includes('No')) {
    if (response == 'No') {
      return
    }
    return Promise.reject(new OpenReviewError({ name: 'Error', message: unavailableInvitationMessage }))
  }

  if (edge && (label || '').startsWith('Declined') && response == 'No') {
    return
  }

  const edgeIsDeleted = edge && edge.ddate && Number(edge.ddate) <= Date.now()
  if (edge && (edgeIsDeleted || label == 'Accepted' || label == 'Conflict Detected' || label == 'Pending Sign Up' || label == 'Expired' || label == 'Superseded' || (label || '').startsWith('Declined'))) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: unavailableInvitationMessage }))
  }

  const isLoggedInProfileResponse = (note.signatures || []).some((signature) => signature && signature.startsWith('~'))
  if (response == 'Yes' && !isLoggedInProfileResponse) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: {{MESSAGE_TEMPLATE_JSON:recruitment/accept_unresolved.txt}} }))
  }

  if (response == 'Yes') {
    return
  }

  return
}
