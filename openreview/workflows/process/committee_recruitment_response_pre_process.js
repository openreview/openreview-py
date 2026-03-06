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