async function process(client, edit, invitation) {
  client.throwErrors = true

  const { groups: domainGroups } = await client.getGroups({ id: invitation.domain })
  const domain = domainGroups[0]
  const { groups: committeeGroups } = await client.getGroups({ id: invitation.content.committee_id?.value })
  const committee = committeeGroups[0]
  const committeeRole = committee.content.committee_role?.value
  const committeeInvitedId = domain.content[`${committeeRole}_invited_id`]?.value
  const venueId = domain.content.venue_id?.value
  const committeeName = domain.content[`${committeeRole}_name`]?.value

  const note = edit.note

  const hashSeed = invitation.content.hash_seed?.value
  const user = decodeURIComponent(note.content.user.value)

  const hashkey = crypto.createHmac('sha256', hashSeed)
                      .update(user)
                      .digest('hex');

  if (hashkey != note.content.key.value) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'Wrong key, please refer back to the recruitment email' }))
  }

  const { count } = await client.getGroups({ id: committeeInvitedId, member: user })

  if (count == 0) {
    return Promise.reject(new OpenReviewError({ name: 'Error', message: 'User not in invited group, please accept the invitation using the email address you were invited with' }))
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