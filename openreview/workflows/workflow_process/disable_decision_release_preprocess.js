async function process(client, edit, invitation) {
  client.throwErrors = true

  const invitationId = edit.invitation?.id
  if (!invitationId || typeof edit.invitation.ddate !== 'number' || !invitationId.includes('_Release')) {
    return
  }

  const { groups } = await client.getGroups({ id: invitation.domain })
  const domain = groups[0]
  const decisionName = domain.content?.decision_name?.value || 'Decision'
  const decisionReleaseId = `${domain.id}/-/${decisionName}_Release`

  if (invitationId !== decisionReleaseId && !invitationId.startsWith(`${decisionReleaseId}/`)) {
    return
  }

  const { invitations } = await client.getInvitations({ prefix: `${domain.id}/-/`, type: 'invitation', domain: domain.id })
  const revisionInvitation = invitations.find((inv) =>
    !inv.ddate &&
    inv.content?.revision_process_script &&
    inv.content?.source?.value?.with_decision_accept === true
  )

  if (revisionInvitation) {
    const revisionName = revisionInvitation.id.split('/-/').pop().replaceAll('_', ' ')
    const releaseName = `${decisionName}_Release`.replaceAll('_', ' ')
    return Promise.reject(new OpenReviewError({ name: 'Error', message: `${revisionName} must be disabled before disabling ${releaseName}. Please disable ${revisionName} first.` }))
  }
}
