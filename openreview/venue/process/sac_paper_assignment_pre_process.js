async function process(client, edge, invitation) {
    client.throwErrors = false
  
    const { groups } = await client.getGroups({ id: edge.domain })
    const domain = groups[0]
    const venueId = domain.id
    const submissionName = domain.content.submission_name?.value
    const sacsName = invitation.content.reviewers_name?.value

    const { notes } = await client.getNotes({ id: edge.head })
    const submission = notes[0]
    const submissionGroupId = `${venueId}/${submissionName}${submission.number}`

    if (!edge.ddate) {
        const { count } = await client.getGroups({ id: `${submissionGroupId}/${sacsName}` })
        if ( count === 0) {
          return Promise.reject(new OpenReviewError({ name: 'Error', message: `Can not make assignment, submission ${sacsName} group not found.` }))
        }
        return
      }
}