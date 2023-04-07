async function process(client, edge, invitation) {
  client.throwErrors = true

  const { groups } = await client.getGroups({ id: edge.domain })
  const domain = groups[0]
  const venue_id = domain.id
  const submission_name = domain.content.submission_name.value
  const review_name = invitation.content.review_name.value
  const reviewers_anon_name = invitation.content.reviewers_anon_name.value

  if (!review_name) {
    return
  }

  if (edge.ddate) {

    const { notes } = await client.getNotes({ id: edge.head })
    const submission = notes[0]
    const submissionGroupId = `${venue_id}/${submission_name}${submission.number}`

    const { groups } = await client.getGroups({ prefix: `${submissionGroupId}/${reviewers_anon_name}`, signatory: edge.tail })

    if (groups.length == 0) { 
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can remove assignment, signatory groups not found for ${edge.tail}` }))
    }

    const { count } = await client.getNotes({ invitation: `${submissionGroupId}/-/` + review_name, signatures: groups[0].id })

    if (count > 0) {
      return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not remove assignment, the user ${edge.tail} already posted a ${review_name.replace('_', ' ')}` }))
    }

  }

}

