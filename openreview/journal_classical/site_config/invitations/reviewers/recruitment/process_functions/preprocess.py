async function process(client, edit, invitation) {
  client.throwErrors = true

  const hashSeed = '4567'
  const recruitmentInviteId = 'JMLR/Reviewers/-/Recruitment_Invite'
  const acceptedGroupId = 'JMLR/Reviewers'
  const note = edit.note
  const user = decodeURIComponent(note.content.user.value)
  const edgeId = note.content.edge_id.value
  const response = note.content.response.value
  const hashkey = crypto.createHmac('sha256', hashSeed)
    .update(edgeId + ':' + user)
    .digest('hex')

  if (hashkey !== note.content.key.value) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: {{MESSAGE_TEMPLATE_JSON:recruitment/invitation_unavailable.txt}} }))
  }

  const { edges } = await client.getEdges({ invitation: recruitmentInviteId, head: acceptedGroupId, tail: user, trash: true })
  const edge = (edges || []).find((candidate) => candidate.id === edgeId) ||
    (edges || []).find((candidate) => candidate.label === 'Invitation Sent') ||
    (edges || [])[0]

  if (!edge) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: {{MESSAGE_TEMPLATE_JSON:recruitment/invitation_unavailable.txt}} }))
  }

  const label = edge.label || ''
  const finalLabels = ['Accepted', 'Conflict Detected', 'Pending Sign Up', 'Expired', 'Superseded']
  const edgeIsDeleted = edge.ddate && Number(edge.ddate) <= Date.now()
  if (edgeIsDeleted || finalLabels.indexOf(label) >= 0 || label.startsWith('Declined')) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: {{MESSAGE_TEMPLATE_JSON:recruitment/invitation_unavailable.txt}} }))
  }

  const isLoggedInProfileResponse = (note.signatures || []).some((signature) => signature && signature.startsWith('~'))
  if (response === 'Yes' && !isLoggedInProfileResponse) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: {{MESSAGE_TEMPLATE_JSON:recruitment/accept_unresolved.txt}} }))
  }

  if (response === 'Yes') {
    return
  }

  if (response === 'No') {
    return
  }

  return Promise.reject(new OpenReviewError({ name: 'Error', message: {{MESSAGE_TEMPLATE_JSON:recruitment/invitation_unavailable.txt}} }))
}
