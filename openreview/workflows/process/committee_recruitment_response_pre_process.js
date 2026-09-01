async function process(client, edit, invitation) {
  client.throwErrors = true

  const { groups: domainGroups } = await client.getGroups({ id: invitation.domain })
  const domain = domainGroups[0]
  const { groups: committeeGroups } = await client.getGroups({ id: invitation.content.committee_id?.value })
  const committee = committeeGroups[0]
  const committeeRole = committee.content.committee_role?.value
  const venueId = domain.id
  const committeeName = domain.content[`${committeeRole}_name`]?.value

  const note = edit.note
  const user = edit.signatures[0]

  if (note.content.response.value == 'Yes') {
    const overlapCommitteeIds = invitation.content.overlap_committee_ids?.value ?? []
    const shortPhrase = domain.content.subtitle?.value
    const committeePrettyName = invitation.content.committee_pretty_name?.value

    for (const overlapCommitteeId of overlapCommitteeIds) {
      const { groups: overlapGroups } = await client.getGroups({ id: overlapCommitteeId, member: user })
      if (overlapGroups.length > 0) {
        const overlapPrettyName = overlapGroups[0].content?.committee_pretty_name?.value ?? Tools.prettyId(overlapCommitteeId, true)
        return Promise.reject(new OpenReviewError({ name: 'Error', message: `You have already accepted an invitation to serve as ${overlapPrettyName} for ${shortPhrase}. If you would like to change your decision and serve as ${committeePrettyName}, please decline the invitation to be ${overlapPrettyName} and then accept the invitation to be ${committeePrettyName}.` }))
      }
    }
    return
  }

  if (note.content.response.value != 'No') {
    return
  }

  const { groups } = await client.getGroups({ prefix: venueId, member: user })
  for(const group of groups) {
    if (group.id.match(venueId + '/.*[0-9]/' + committeeName)) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: 'You have already been assigned to a paper. Please contact the paper area chair or program chairs to be unassigned.' }))
    }
  }

}