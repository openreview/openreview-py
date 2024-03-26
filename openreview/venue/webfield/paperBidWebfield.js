// Webfield component
const committeeName = entity.content.committee_name?.value
const affinityScoreId = domain.content[`${committeeName.toLowerCase()}_affinity_score_id`]?.value

return {
  component: 'BidConsole',
  version: 1,
  properties: {
    header: {
      title: `${(committeeName.endsWith('s') ? committeeName.slice(0, -1) : committeeName).replaceAll('_', ' ')} Bidding Console`,
      instructions: `**Instructions:**

- Please indicate your **level of interest** in reviewing the submitted papers below, on a scale from "Very Low" interest to "Very High" interest.
- Please bid on as many papers as possible to ensure that your preferences are taken into account.
- Use the search field to filter papers by keyword or subject area.
- Ensure that you have at least **${entity.minReplies} bids**.

**A few tips:**

- Papers for which you have a conflict of interest are not shown.
- Positive bids ("High" and "Very High") will, in most cases, increase the likelihood that you will be assigned that paper.
- Negative bids ("Low" and "Very Low") will, in most cases, decrease the likelihood that you will be assigned that paper.
${affinityScoreId ? '- Papers are sorted based on keyword similarity with the papers that you provided in the Expertise Selection Interface.' : ''}`
    },
    venueId: domain.id,
    submissionVenueId: domain.content.submission_venue_id?.value,
    scoreIds: affinityScoreId ? [affinityScoreId] : [],
    conflictInvitationId: domain.content[`${committeeName.toLowerCase()}_conflict_id`]?.value,
    subjectAreas: domain.content.subject_areas?.value
  }
}
